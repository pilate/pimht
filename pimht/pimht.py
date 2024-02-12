import functools
import importlib.metadata
import io
import quopri
import typing

from . import util

try:
    import cchardet as chardet
except ModuleNotFoundError:
    import chardet


__version__ = importlib.metadata.version("pimht")


class MHTMLPart:
    """Part of an MHTML archive."""

    def __init__(self, headers: dict, content: str):
        self.headers = headers
        self.content = content

    @functools.cached_property
    def content_type(self) -> str:
        """Content-type of the MHTML part."""
        return self.headers.get("Content-Type").split(";")[0]

    @functools.cached_property
    def is_text(self) -> bool:
        """Whether or not the parts content-type begins with 'text'."""
        return self.content_type.startswith("text/")

    @functools.cached_property
    def raw(self) -> bytes:
        """The raw (bytes) content of the MHTML part."""
        return self.content

    @functools.cached_property
    def text(self) -> str:
        """
        String representation of the MHTML part.
        Raises TypeError if the part cannot be decoded.
        """
        if not self.is_text:
            raise TypeError("MHTMLPart is not text")

        charset = chardet.detect(self.raw)
        return self.raw.decode(charset["encoding"] or "utf-8", "ignore")

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} headers={self.headers}>"


class MHTML:  # pylint: disable=too-few-public-methods
    """
    MHTML archive.
    Objects are iterable to allow processing/inspection of archive contents.
    """

    def __init__(self, mhtml: typing.TextIO):
        self.fp = mhtml
        self.headers = util.parse_headers(mhtml)

    def __iter__(self) -> typing.Iterator[MHTMLPart]:
        headers = self.headers
        boundary = util.find_boundary(headers["Content-Type"])

        data = []
        for line in self.fp:
            if line.startswith(boundary):
                if data:
                    # last newline is part of new boundary
                    data[-1] = data[-1][:-1]
                    decoded_data = quopri.decodestring("".join(data))
                    yield MHTMLPart(headers, decoded_data)
                    data.clear()

                headers = util.parse_headers(self.fp)
                continue

            data.append(line)

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} headers={self.headers}>"


def from_bytes(mhtml_bytes: bytes) -> MHTML:
    """Parse bytes as an MHTML object."""
    fileobj = io.StringIO(mhtml_bytes.decode("ascii"))
    return MHTML(fileobj)


def from_string(mhtml_str: str) -> MHTML:
    """Parse a string as an MHTML object."""
    return MHTML(io.StringIO(mhtml_str))


def from_fileobj(fileobj: typing.IO) -> MHTML:
    """Parse a file object as an MHTML object."""
    if "b" in fileobj.mode:
        data = fileobj.read()
        fileobj = io.StringIO(data.decode("ascii"))

    return MHTML(fileobj)


def from_filename(filename: str) -> MHTML:
    """Parse the contents of a file path as an MHTML object."""
    with open(filename, "rb") as fileobj:
        return from_fileobj(fileobj)
