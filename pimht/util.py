import typing


def parse_headers(fp: typing.TextIO) -> typing.Mapping[str, str]:
    """
    Read lines and split into key/value pairs from fp until newline.
    Supports tab being used to continue previous header line.
    """
    headers = {}

    key = None
    for line in fp:
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


def parse_content_type(header: str) -> list:
    if ";" not in header:
        return [header]

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


def find_boundary(content_type: str) -> str:
    """Search content-type header for a boundary"""
    if ";" not in content_type:
        raise TypeError("No parts in Content-Type")

    if "boundary=" not in content_type:
        raise TypeError("No boundary in Content-Type")

    parsed_content = parse_content_type(content_type)

    if isinstance(parsed_content, list):
        for field in parsed_content:
            if isinstance(field, tuple):
                key, value = field
                if key == "boundary":
                    return f"--{value}"

    raise TypeError("No boundary in Content-Type")
