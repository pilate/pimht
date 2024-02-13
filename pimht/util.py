import email.header
import re
import typing


BOUND_RE = re.compile(r";boundary=(['\"])([^'\"]+)\1")


def read_headers(fp: typing.TextIO) -> typing.Mapping[str, str]:
    """
    Read lines and split into key/value pairs from fp until newline.
    Supports tab being used to continue previous header line.
    """
    headers = {}

    key = None
    while line := fp.readline():
        line = line.rstrip()
        if not line:
            break

        # continuation
        if line[0] in (" ", "\t"):
            if key:
                headers[key] += line[1:]
            continue

        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()

    # rfc 2047 decoding
    for key, value in headers.items():
        if "=?" in value:
            new_value = ""
            for byte_str, encoding in email.header.decode_header(value):
                if not encoding:
                    new_value += byte_str
                    continue
                new_value += byte_str.decode(encoding)
            headers[key] = new_value

    return headers


def find_boundary(content_type: str) -> str:
    if match := BOUND_RE.search(content_type):
        return "--" + match.group(2)

    raise TypeError("No boundary in Content-Type")
