import email
import email.message
import sys
import typing

try:
    import cchardet as chardet
except ModuleNotFoundError:
    import chardet


class MHTMLPart:
    def __init__(self, message: email.message.Message):
        self.message = message

        self.headers = dict(message)
        self.raw = message.get_payload()

        self.content_type = self.message.get_content_type()
        self.is_text = self.content_type.startswith("text/")

    @property
    def charset(self) -> dict:
        return chardet.detect(self.raw)

    @property
    def text(self) -> str:
        if not self.is_text:
            raise TypeError("MHTMLPart is not text")

        return self.raw.decode(self.charset["encoding"], "ignore")

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
    return MHTML(email.message_from_bytes(mhtml_bytes))


def from_string(mhtml_str: str) -> MHTML:
    return MHTML(email.message_from_string(mhtml_str))


def from_filename(filename: str) -> MHTML:
    with open(filename, "rb") as fileobj:
        return MHTML(email.message_from_binary_file(fileobj))


def from_fileobj(fileobj: typing.IO) -> MHTML:
    if "b" in fileobj.mode:
        return MHTML(email.message_from_binary_file(fileobj))

    return MHTML(email.message_from_file(fileobj))


def main():
    filename = sys.argv[1]

    mht = from_filename(filename)
    for thing in mht:
        print(thing)


if __name__ == "__main__":
    main()
