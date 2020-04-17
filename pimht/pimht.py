import email
import sys

try:
    import cchardet as chardet
except ImportError:
    import chardet



class MHTMLPart(object):

    def __init__(self, message):
        self.message = message

        self.headers = dict(message)
        self.raw = message.get_payload(decode=True)

        self.content_type = self.message.get_content_type()
        self.is_text = self.content_type.startswith('text/')


    @property
    def charset(self):
        return chardet.detect(self.raw)


    @property
    def text(self):
        if not self.is_text:
            raise Exception('Part is not text')

        return self.raw.decode(self.charset['encoding'], 'ignore')


    def __str__(self):
        return f'<{self.__class__.__name__} headers={self.headers}>'


class MHTML(object):

    def __init__(self, message):
        self.message = message

        if not self.message.is_multipart():
            raise TypeError('Not a valid MHTML file')


    def __iter__(self):
        for msg in self.message.walk():
            if msg.get_content_maintype() == 'multipart':
                continue

            yield MHTMLPart(msg)



def from_bytes(literal):
    return MHTML(email.message_from_bytes(literal))


def from_string(string):
    return MHTML(email.message_from_string(string))


def from_filename(filename):
    fileobj = open(filename, 'rb')
    return MHTML(email.message_from_binary_file(fileobj))


def from_fileobj(fileobj):
    if 'b' in fileobj.mode:
        return MHTML(email.message_from_binary_file(fileobj))
    else:
        return MHTML(email.message_from_file(fileobj))


def main():
    filename = sys.argv[1]

    # mht = from_string(open(filename, 'r').read())
    # for thing in mht:
    #     print(thing)

    # mht = from_bytes(open(filename, 'rb').read())
    # for thing in mht:
    #     print(thing)

    # mht = from_filename(filename)
    # for thing in mht:
    #     print(thing)

    mht = from_fileobj(open(filename, 'rb'))
    for thing in mht:
        print(thing)


main() if __name__ == '__main__' else None
