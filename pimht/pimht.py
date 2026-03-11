import functools
import importlib.metadata
import quopri
import typing

from . import util

try:
    import pybase64 as base64
except ModuleNotFoundError:
    import base64

try:
    import cchardet as chardet
except ModuleNotFoundError:
    import chardet


__version__ = importlib.metadata.version("pimht")


class MHTMLPart:
    """Part of an MHTML archive."""

    def __init__(self, headers: dict, content: bytes):
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

        # Try charset from Content-Type header before expensive chardet
        ct = self.headers.get("Content-Type", "")
        for param in ct.split(";")[1:]:
            param = param.strip()
            if param.lower().startswith("charset="):
                charset = param.split("=", 1)[1].strip().strip("'\"")
                return self.raw.decode(charset, "ignore")

        detected = chardet.detect(self.raw)
        return self.raw.decode(detected["encoding"] or "utf-8", "ignore")

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} headers={self.headers}>"


class MHTML:  # pylint: disable=too-few-public-methods
    """
    MHTML archive.
    Objects are iterable to allow processing/inspection of archive contents.
    """

    def __init__(self, content: bytes):
        # Normalize line endings (matches text-mode behavior, simplifies parsing)
        content = content.replace(b"\r\n", b"\n")

        sep = content.find(b"\n\n")
        self.headers = util.parse_headers(content[:sep])
        self.boundary = util.find_boundary(self.headers["Content-Type"])
        self._body = content[sep + 2:]

    def __iter__(self) -> typing.Iterator[MHTMLPart]:
        segments = self._body.split(self.boundary)
        for segment in segments[1:]:
            if segment[:2] == b"--":
                break

            sep = segment.find(b"\n\n")
            if sep == -1:
                continue

            # Skip leading \n after boundary marker
            headers = util.parse_headers(segment[1:sep])
            content = segment[sep + 2:]

            # Remove trailing newline (part of next boundary delimiter)
            if content.endswith(b"\n"):
                content = content[:-1]

            yield MHTMLPart(headers, content)

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} headers={self.headers}>"


def from_bytes(mhtml_bytes: bytes) -> MHTML:
    """Parse bytes as an MHTML object."""
    return MHTML(mhtml_bytes)


def from_string(mhtml_str: str) -> MHTML:
    """Parse a string as an MHTML object."""
    return MHTML(mhtml_str.encode("ascii"))


def from_fileobj(fileobj: typing.IO) -> MHTML:
    """Parse a file object as an MHTML object."""
    data = fileobj.read()
    if isinstance(data, str):
        data = data.encode("ascii")
    return MHTML(data)


def from_filename(filename: str) -> MHTML:
    """Parse the contents of a file path as an MHTML object."""
    with open(filename, "rb") as f:
        return MHTML(f.read())
