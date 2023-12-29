import email
import email.message
import email.parser
import sys
import typing
from functools import cached_property
from importlib.metadata import version

try:
    import cchardet as chardet
except ModuleNotFoundError:
    import chardet


__version__ = version("pimht")


class FasterParser(email.parser.Parser):
    """
    Replacement for email.parser.Parser that removes 8kb chunking.
    https://stackoverflow.com/questions/3543118/python-email-message-from-string-performance-with-large-data-in-email-body
    """

    def parse(self, fp, headersonly=False):
        feedparser = email.parser.FeedParser(self._class, policy=self.policy)
        if headersonly:
            feedparser._set_headersonly()
        while data := fp.read():  # removed read size limit
            feedparser.feed(data)
        return feedparser.close()


class FasterBytesParser(email.parser.BytesParser):
    """Replacement for email.parser.BytesParser that removes 8kb chunking."""

    def __init__(self, *args, **kwargs):
        self.parser = FasterParser(*args, **kwargs)


class MHTMLPart:
    """Part of an MHTML archive."""

    def __init__(self, message: email.message.Message):
        self.message = message

        self.headers = dict(message)
        """Headers for the MHTML part."""

    @cached_property
    def content_type(self) -> str:
        """Content-type of the MHTML part."""
        return self.message.get_content_type()

    @cached_property
    def is_text(self) -> bool:
        """Whether or not the parts content-type begins with 'text'."""
        return self.content_type.startswith("text/")

    @cached_property
    def raw(self) -> bytes:
        """The raw (bytes) content of the MHTML part."""
        return self.message.get_payload(decode=True) or b""

    @cached_property
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


class MHTML:
    """
    MHTML archive.
    Objects are iterable to allow processing/inspection of archive contents.
    """

    def __init__(self, message: email.message.Message):
        self.message = message

        if not self.message.is_multipart():
            raise TypeError("Not a valid MHTML file")

    def __iter__(self) -> typing.Iterator[MHTMLPart]:
        for msg in self.message.walk():
            yield MHTMLPart(msg)


def from_bytes(mhtml_bytes: bytes) -> MHTML:
    """Parse bytes as an MHTML object."""
    message = FasterBytesParser().parsebytes(mhtml_bytes)
    return MHTML(message)


def from_string(mhtml_str: str) -> MHTML:
    """Parse a string as an MHTML object."""
    message = FasterParser().parsestr(mhtml_str)
    return MHTML(message)


def from_fileobj(fileobj: typing.IO) -> MHTML:
    """Parse a file object as an MHTML object."""
    if "b" in fileobj.mode:
        message = FasterBytesParser().parse(fileobj)
    else:
        message = FasterParser().parse(fileobj)
    return MHTML(message)


def from_filename(filename: str) -> MHTML:
    """Parse the contents of a file path as an MHTML object."""
    with open(filename, "rb") as fileobj:
        return from_fileobj(fileobj)


def main():
    filename = sys.argv[1]

    mht = from_filename(filename)
    for thing in mht:
        print(thing)


if __name__ == "__main__":
    main()
