import pathlib

from pimht import (
    __version__,
    from_bytes,
    from_string,
    from_filename,
    from_fileobj,
    MHTML,
    MHTMLPart,
)


EXAMPLE_PATH = filepath = pathlib.Path(__file__).parent / "example_com.mhtml"
EXAMPLE_URL = "https://www.example.com/"


def test_parsers():
    with open(EXAMPLE_PATH, "rb") as fp:
        bytes_data = fp.read()

    bytes_mhtml = from_bytes(bytes_data)
    assert isinstance(bytes_mhtml, MHTML)

    str_mhtml = from_string(bytes_data.decode("utf-8"))
    assert isinstance(str_mhtml, MHTML)

    filename_mhtml = from_filename(EXAMPLE_PATH)
    assert isinstance(filename_mhtml, MHTML)

    with open(EXAMPLE_PATH, "r", encoding="utf-8") as fp:
        str_file_mhtml = from_fileobj(fp)
        assert isinstance(str_file_mhtml, MHTML)

    with open(EXAMPLE_PATH, "rb") as fp:
        bytes_file_mhtml = from_fileobj(fp)
        assert isinstance(bytes_file_mhtml, MHTML)


def test_parsing():
    mhtml = from_filename(EXAMPLE_PATH)
    counter = 0
    for counter, part in enumerate(mhtml, start=1):
        assert isinstance(part, MHTMLPart)
        assert isinstance(part.headers, dict)

        assert mhtml.headers.get("From") == "<Saved by Blink>"
        assert mhtml.headers.get("Snapshot-Content-Location") == EXAMPLE_URL

        if counter == 1:
            assert part.headers.get("Content-Location") == EXAMPLE_URL
            assert part.content_type == "text/html"
            assert part.is_text is True
            assert isinstance(part.raw, bytes)
            assert part.raw.startswith(b"<!DOCTYPE html><html>")
            assert part.text.startswith("<!DOCTYPE html><html>")

        elif counter == 2:
            assert part.content_type == "text/css"
            assert part.is_text is True
            assert isinstance(part.raw, bytes)
            assert part.raw.startswith(b'@charset "utf-8";')
            assert part.text.startswith('@charset "utf-8";')

        elif counter == 3:
            assert part.content_type == "image/png"
            assert part.is_text is False
            assert isinstance(part.raw, bytes)
            assert part.raw.startswith(b'\x89PNG')

    assert counter == 3
