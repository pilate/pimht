"""Module to simplify handling of MHTML archives."""

from .pimht import (
    __version__,
    from_bytes,
    from_string,
    from_filename,
    from_fileobj,
    MHTML,
    MHTMLPart,
)
