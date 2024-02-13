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
        if line.startswith("\t"):
            if key:
                headers[key] += line[1:]
            continue

        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()

    return headers


def find_boundary(content_type: str) -> str:
    if match := BOUND_RE.search(content_type):
        return "--" + match.group(2)

    raise TypeError("No boundary in Content-Type")
