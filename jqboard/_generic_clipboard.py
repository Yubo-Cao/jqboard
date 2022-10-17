from io import BytesIO
from typing import Any

from lxml import etree
from PIL import Image

from jqboard import ClipboardFormat


def format_output(data: bytes, fmt: ClipboardFormat) -> Any:
    if fmt == ClipboardFormat.TEXT or fmt == ClipboardFormat.HTML:
        return data.decode("utf-8")
    elif fmt == ClipboardFormat.IMAGE:
        return Image.open(BytesIO(data))
    else:
        raise ValueError("Invalid format")


def format_input(data: Any, fmt: ClipboardFormat) -> bytes:
    if fmt == ClipboardFormat.TEXT or fmt == ClipboardFormat.HTML:
        return data.encode("utf-8")
    elif fmt == ClipboardFormat.IMAGE:
        buf = BytesIO()
        data.save(buf, "PNG")
        return buf.getvalue()
    else:
        raise ValueError("Invalid format")


def guess_format(
    data: Any, default_fmt: ClipboardFormat = ClipboardFormat.TEXT
) -> ClipboardFormat:
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
