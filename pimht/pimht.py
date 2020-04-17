import email

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

    def __init__(self, filename=None, fileobj=None, string=None):
        if filename:
            fileobj = open(filename, 'r')

        if fileobj:
            self.message = email.message_from_file(fileobj)
        elif string:
            self.message = email.message_from_string(string)
        else:
            raise TypeError('Nothing to open')

        if not self.message.is_multipart():
            raise TypeError('Not a valid MHTML file')


    def __iter__(self):
        for msg in self.message.walk():
            if msg.get_content_maintype() == 'multipart':
                continue

            yield MHTMLPart(msg)


def from_string(string):
    return MHTML(string=string)


def from_filename(filename):
    return MHTML(filename=filename)


def from_fileobj(fileobj):
    return MHTML(fileobj=fileobj)


def main():
    # mht = from_string(open('../196a14d7e5d5b290eff218cf86397eec54fcbdc85886fc72bfebe3c24cc84c9f.mhtml', 'r').read())
    # mht = from_filename('../196a14d7e5d5b290eff218cf86397eec54fcbdc85886fc72bfebe3c24cc84c9f.mhtml')
    mht = from_fileobj(open('../196a14d7e5d5b290eff218cf86397eec54fcbdc85886fc72bfebe3c24cc84c9f.mhtml', 'r'))
    for thing in mht:
        print(thing)


main() if __name__ == '__main__' else None
