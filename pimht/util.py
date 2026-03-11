import re


BOUND_RE = re.compile(r";\s*boundary=(['\"])([^'\"]+)\1")


def parse_headers(raw: bytes) -> dict[str, str]:
    """
    Parse MIME headers from raw bytes into a str dict.
    Supports tab/space continuation of previous header line.
    """
    headers = {}

    key = None
    for line in raw.decode("ascii").split("\n"):
        if not line:
            continue

        # continuation
        if line[0] in (" ", "\t"):
            if key:
                headers[key] += line[1:]
            continue

        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()

    return headers


def find_boundary(content_type: str) -> bytes:
    """Extract and return the MIME boundary as bytes."""
    if match := BOUND_RE.search(content_type):
        return b"--" + match.group(2).encode("ascii")

    raise TypeError("No boundary in Content-Type")
