import functools
import importlib.metadata
import io
import quopri
import typing

try:
    import cchardet as chardet
except ModuleNotFoundError:
    import chardet


__version__ = importlib.metadata.version("pimht")


def parse_content_type(header):
    if ";" not in header:
        return header

    content_type = []
    for part in header.split(";"):
        if "=" not in part:
            content_type.append(part)
            continue
        key, value = part.split("=")
        if value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        elif value.startswith('"') and value.endswith('"'):
            value = value[1:-1]

        content_type.append((key.strip(), value.strip()))
    return content_type


def parse_headers(fp):
    headers = {}

    key = None
    for line in fp:
        line = line.rstrip()
        if not line:
            break

        # continuation
        if line.startswith("\t"):
            if key:
                headers[key] += line[1:].strip()
            continue

        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()

    if "Content-Type" in headers:
        headers["Content-Type"] = parse_content_type(headers["Content-Type"])

    return headers


class MHTMLPart:
    """Part of an MHTML archive."""

    def __init__(self, headers: dict, content: str):
        self.headers = headers
        self.content = content

    @functools.cached_property
    def content_type(self) -> str:
        """Content-type of the MHTML part."""
        return self.headers.get("Content-Type")

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
        self.mhtml_fp = mhtml

        self.headers = parse_headers(mhtml)

        type_headers = self.headers["Content-Type"]
        self.content_type = type_headers[0]

        for field in type_headers:
            if isinstance(field, tuple):
                key, value = field
                if key == "boundary":
                    self.boundary_start = f"--{value}"

        # consume newline of first mhtml part
        mhtml.readline()

    def __iter__(self) -> typing.Iterator[MHTMLPart]:
        data = []

        for line in self.mhtml_fp:
            if line.startswith(self.boundary_start):
                if data:
                    # last newline is part of new boundary
                    data[-1] = data[-1][:-1]

                    yield MHTMLPart(headers, quopri.decodestring("".join(data)))

                data = []
                headers = parse_headers(self.mhtml_fp)
                continue

            data.append(line)


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
