from io import BytesIO
from typing import Any, cast, Optional

from PIL import Image
from lxml import etree

from jqboard import ClipboardFormat


def format_output(data: bytes, fmt: ClipboardFormat) -> Any:
    match fmt:
        case ClipboardFormat.TEXT | ClipboardFormat.HTML:
            return data.decode("utf-8")
        case ClipboardFormat.IMAGE:
            return Image.open(BytesIO(data))


def format_input(data: Any, fmt: ClipboardFormat) -> bytes:
    match fmt:
        case ClipboardFormat.TEXT | ClipboardFormat.HTML:
            return data.encode("utf-8")
        case ClipboardFormat.IMAGE:
            cast(Image.Image, data).save(buf := BytesIO(), "PNG")
            return buf.getvalue()


def guess_format(data: Any, default_fmt: ClipboardFormat = ClipboardFormat.TEXT) -> ClipboardFormat:
    if isinstance(data, str):
        try:
            etree.XML(data)
            return ClipboardFormat.HTML
        except etree.XMLSyntaxError:
            return ClipboardFormat.TEXT
    elif isinstance(data, Image.Image):
        return ClipboardFormat.IMAGE
    elif isinstance(data, bytes):
        try:
            return guess_format(data.decode("utf-8"))
        except UnicodeDecodeError:
            return ClipboardFormat.IMAGE
    else:
        return default_fmt
