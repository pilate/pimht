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

    def __setattr__(self, name, value):
        if name == "raw":
            encoding = self.headers.get("Content-Transfer-Encoding")
            if encoding == "base64":
                self.content = base64.encodebytes(value).rstrip(b"\n")
            elif encoding == "quoted-printable":
                self.content = quopri.encodestring(value).rstrip(b"\n")
            else:
                raise ValueError(f"Unknown mhtml part encoding: {encoding}")

            self.__dict__["raw"] = value
            self.__dict__.pop("text", None)

        elif name == "text":
            charset = self.charset or "utf-8"
            self.raw = value.encode(charset)
            self.__dict__["text"] = value

        else:
            super().__setattr__(name, value)

    @functools.cached_property
    def content_type(self) -> str:
        """Content-type of the MHTML part."""
        return self.headers.get("Content-Type").split(";")[0]

    @functools.cached_property
    def is_text(self) -> bool:
        """Whether or not the parts content-type begins with 'text'."""
        return self.content_type.startswith("text/")

    @functools.cached_property
    def charset(self):
        """Charset from Content-Type header, or None."""
        ct = self.headers.get("Content-Type", "")
        for param in ct.split(";")[1:]:
            param = param.strip()
            if param.lower().startswith("charset="):
                return param.split("=", 1)[1].strip().strip("'\"")
        return None

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

        charset = self.charset
        if charset:
            return self.raw.decode(charset, "ignore")

        detected = chardet.detect(self.raw)
        return self.raw.decode(detected["encoding"] or "utf-8", "ignore")

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} headers={self.headers}>"


class MHTML:
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

    @functools.cached_property
    def parts(self) -> list:
        """All parts in the MHTML archive."""
        result = []
        segments = self._body.split(self.boundary)
        for segment in segments[1:]:
            if segment[:2] == b"--":
                break

            sep = segment.find(b"\n\n")
            if sep == -1:
                continue

            headers = util.parse_headers(segment[1:sep])
            content = segment[sep + 2:]
            if content.endswith(b"\n"):
                content = content[:-1]

            result.append(MHTMLPart(headers, content))
        return result

    def __iter__(self) -> typing.Iterator[MHTMLPart]:
        return iter(self.parts)

    def to_bytes(self) -> bytes:
        """Serialize the MHTML archive to bytes."""
        chunks = []

        # Global headers
        for key, value in self.headers.items():
            chunks.append(f"{key}: {value}\r\n".encode("ascii"))
        chunks.append(b"\r\n")

        # Parts
        for part in self.parts:
            chunks.append(self.boundary + b"\r\n")
            for key, value in part.headers.items():
                chunks.append(f"{key}: {value}\r\n".encode("ascii"))
            chunks.append(b"\r\n")
            chunks.append(part.content.replace(b"\n", b"\r\n"))
            chunks.append(b"\r\n")

        # Closing boundary
        chunks.append(self.boundary + b"--\r\n")

        return b"".join(chunks)

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
