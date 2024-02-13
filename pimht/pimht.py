import base64
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
        encoding = self.headers.get("Content-Transfer-Encoding")
        if encoding == "base64":
            return base64.b64decode(self.content)
        if encoding == "quoted-printable":
            return quopri.decodestring(self.content)
        raise ValueError(f"Unknown mhtml part encoding: {encoding}")

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

        self.fp.seek(0)
        self.headers = util.read_headers(self.fp)
        self.boundary = util.find_boundary(self.headers["Content-Type"])

        # find the end of the container
        self._fp_start = 0
        while line := self.fp.readline():
            if line.startswith(self.boundary):
                break
            self._fp_start = self.fp.tell()

    def __iter__(self) -> typing.Iterator[MHTMLPart]:
        self.fp.seek(self._fp_start)
        data = []
        while line := self.fp.readline():
            if line.startswith(self.boundary):
                if data:
                    # last newline is part of new boundary
                    data[-1] = data[-1][:-1]
                    yield MHTMLPart(headers, "".join(data))
                    data.clear()

                headers = util.read_headers(self.fp)
                continue

            data.append(line)

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} fieobj={self.fp}, headers={self.headers}>"


def from_bytes(mhtml_bytes: bytes) -> MHTML:
    """Parse bytes as an MHTML object."""
    return from_string(mhtml_bytes.decode("ascii"))


def from_string(mhtml_str: str) -> MHTML:
    """Parse a string as an MHTML object."""
    return MHTML(io.StringIO(mhtml_str))


def from_fileobj(fileobj: typing.IO) -> MHTML:
    """Parse a file object as an MHTML object."""
    if "b" in fileobj.mode:
        fileobj = io.TextIOWrapper(fileobj, encoding="ascii")

    return MHTML(fileobj)


def from_filename(filename: str) -> MHTML:
    """Parse the contents of a file path as an MHTML object."""
    return MHTML(open(filename, "r", encoding="ascii"))
