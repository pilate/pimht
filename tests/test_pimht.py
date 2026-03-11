import pathlib

import pytest

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

    assert mhtml.headers.get("From") == "<Saved by Blink>"
    assert mhtml.headers.get("Snapshot-Content-Location") == EXAMPLE_URL

    counter = 0
    for counter, part in enumerate(mhtml, start=1):
        assert isinstance(part, MHTMLPart)
        assert isinstance(part.headers, dict)

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


def test_parts_property():
    mhtml = from_filename(EXAMPLE_PATH)
    assert len(mhtml.parts) == 3
    # .parts and __iter__ return the same objects
    assert list(mhtml) is not mhtml.parts
    for a, b in zip(mhtml, mhtml.parts):
        assert a is b


def test_charset():
    mhtml = from_filename(EXAMPLE_PATH)
    html_part = mhtml.parts[0]
    # example_com.mhtml has charset in Content-Type via quoted-printable encoding
    # CSS part may or may not have charset
    assert html_part.charset is None or isinstance(html_part.charset, str)


def test_round_trip():
    mhtml = from_filename(EXAMPLE_PATH)
    data = mhtml.to_bytes()
    mhtml2 = from_bytes(data)

    assert mhtml.headers == mhtml2.headers
    assert len(mhtml.parts) == len(mhtml2.parts)

    for orig, rt in zip(mhtml.parts, mhtml2.parts):
        assert orig.headers == rt.headers
        assert orig.raw == rt.raw
        if orig.is_text:
            assert orig.text == rt.text


def test_set_text():
    mhtml = from_filename(EXAMPLE_PATH)
    part = mhtml.parts[0]
    original = part.text

    assert "Example Domain" in original
    part.text = original.replace("Example Domain", "Modified Domain")

    assert "Modified Domain" in part.text
    assert "Example Domain" not in part.text

    # round-trip preserves the modification
    mhtml2 = from_bytes(mhtml.to_bytes())
    assert "Modified Domain" in mhtml2.parts[0].text
    assert "Example Domain" not in mhtml2.parts[0].text

    # unmodified parts are identical
    for i in range(1, len(mhtml.parts)):
        assert mhtml.parts[i].raw == mhtml2.parts[i].raw


def test_set_raw():
    mhtml = from_filename(EXAMPLE_PATH)
    png_part = mhtml.parts[2]
    assert png_part.content_type == "image/png"

    png_part.raw = b"\x89PNG\r\n\x1a\nFAKE"
    assert png_part.raw == b"\x89PNG\r\n\x1a\nFAKE"

    # round-trip preserves the modification
    mhtml2 = from_bytes(mhtml.to_bytes())
    assert mhtml2.parts[2].raw == b"\x89PNG\r\n\x1a\nFAKE"


def test_set_text_invalidates_raw_cache():
    mhtml = from_filename(EXAMPLE_PATH)
    part = mhtml.parts[0]

    old_raw = part.raw
    part.text = "completely new content"
    assert part.raw != old_raw
    assert part.text == "completely new content"


def test_set_raw_invalidates_text_cache():
    mhtml = from_filename(EXAMPLE_PATH)
    part = mhtml.parts[0]

    old_text = part.text
    part.raw = b"new raw content"
    assert part.text != old_text
    assert part.raw == b"new raw content"


def test_raw_is_cached():
    mhtml = from_filename(EXAMPLE_PATH)
    part = mhtml.parts[0]
    assert part.raw is part.raw


def test_text_not_text_raises():
    mhtml = from_filename(EXAMPLE_PATH)
    png_part = mhtml.parts[2]
    assert png_part.is_text is False
    with pytest.raises(TypeError):
        _ = png_part.text
