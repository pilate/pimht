import email
import email.message
import email.parser
import sys
import typing

try:
    import cchardet as chardet
except ModuleNotFoundError:
    import chardet


class FasterParser(email.parser.Parser):
    """
    Built-in 'Parser' will only process 8kb at a time
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
    def __init__(self, *args, **kwargs):
        self.parser = FasterParser(*args, **kwargs)


class MHTMLPart:
    def __init__(self, message: email.message.Message):
        self.message = message

        self.headers = dict(message)
        self.raw = message.get_payload(decode=True) or b""

        self.content_type = self.message.get_content_type()
        self.is_text = self.content_type.startswith("text/")

    @property
    def charset(self) -> dict:
        return chardet.detect(self.raw)

    @property
    def text(self) -> str:
        if not self.is_text:
            raise TypeError("MHTMLPart is not text")

        return self.raw.decode(self.charset["encoding"] or "utf-8", "ignore")

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} headers={self.headers}>"


class MHTML:
    def __init__(self, message: email.message.Message):
        self.message = message

        if not self.message.is_multipart():
            raise TypeError("Not a valid MHTML file")

    def __iter__(self) -> typing.Iterator[MHTMLPart]:
        for msg in self.message.walk():
            yield MHTMLPart(msg)


def from_bytes(mhtml_bytes: bytes) -> MHTML:
    message = FasterBytesParser().parsebytes(mhtml_bytes)
    return MHTML(message)


def from_string(mhtml_str: str) -> MHTML:
    message = FasterParser().parsestr(mhtml_str)
    return MHTML(message)


def from_fileobj(fileobj: typing.IO) -> MHTML:
    if "b" in fileobj.mode:
        message = FasterBytesParser().parse(fileobj)
    else:
        message = FasterParser().parse(fileobj)
    return MHTML(message)


def from_filename(filename: str) -> MHTML:
    with open(filename, "rb") as fileobj:
        return from_fileobj(fileobj)


def main():
    filename = sys.argv[1]

    mht = from_filename(filename)
    for thing in mht:
        print(thing)


if __name__ == "__main__":
    main()
