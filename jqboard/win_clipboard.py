import re
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps
from io import BytesIO
from typing import List, Dict, Literal, Tuple, Any

import win32clipboard as clip
from PIL import Image
from lxml import etree

from jqboard._generic_clipboard import guess_format
from jqboard.clipboard import ClipboardFormat, Clipboard, Platform
from jqboard.error import ClipboardError, raise_format_error


def _clipboard_manger_gen():
    clipboard_opened = False

    def clipboard(fn=None):
        nonlocal clipboard_opened
        if isinstance(fn, Callable):
            @wraps(fn)
            def decorator(*args, **kwargs):
                nonlocal clipboard_opened
                if not clipboard_opened:
                    with clipboard():
                        return fn(*args, **kwargs)
                else:
                    return fn(*args, **kwargs)

            return decorator
        else:
            @contextmanager
            def manager():
                nonlocal clipboard_opened
                try:
                    if not clipboard_opened:
                        clip.OpenClipboard()
                        clipboard_opened = True
                    yield
                finally:
                    clip.CloseClipboard()
                    clipboard_opened = False

            return manager()

    return clipboard


_clipboard = _clipboard_manger_gen()


@_clipboard
def _html_format() -> int:
    return clip.RegisterClipboardFormat('HTML Format')


_FORMAT_TO_INT = {
    ClipboardFormat.TEXT: clip.CF_UNICODETEXT,
    ClipboardFormat.IMAGE: clip.CF_DIB,
    ClipboardFormat.HTML: _html_format()
}

_INT_TO_FORMAT = {v: k for k, v in _FORMAT_TO_INT.items()}

_predefined_type = {v: k for k, v in vars(clip).items() if k.startswith('CF_')}


@_clipboard
def _set_clipboard(data, fmt: ClipboardFormat):
    try:
        return clip.SetClipboardData(_FORMAT_TO_INT[fmt], data)
    except:
        pass
    raise ClipboardError(f"Unable to set clipboard data '{fmt}'")


@_clipboard
def _get_clipboard(fmt: ClipboardFormat) -> Any:
    try:
        return clip.GetClipboardData(_FORMAT_TO_INT[fmt])
    except:
        pass
    raise_format_error(fmt)


@_clipboard
def _get_formats() -> List[int]:
    formats = []
    cf = clip.EnumClipboardFormats(0)
    while cf != 0:
        formats.append(cf)
        cf = clip.EnumClipboardFormats(cf)
    return formats


@_clipboard
def _get_format_name(format: int) -> str:
    try:
        return _predefined_type[format]
    except KeyError:
        try:
            return clip.GetClipboardFormatName(format)
        except:
            return "unknown"


@_clipboard
def _get_formats_name(formats: List[int] = ...) -> List[str]:
    if formats is ...:
        return _get_formats_name(_get_formats())
    return [_get_format_name(fmt) for fmt in formats]


def _parser_gen(regex: str, flags: re.RegexFlag = re.MULTILINE | re.VERBOSE) -> Callable[[str], Dict[str, str]]:
    regex = re.compile(regex, flags)

    def parser(string):
        try:
            return regex.match(string).groupdict()
        except AttributeError:
            raise ClipboardError("Invalid HTML clipboard content")

    return parser


_parse_html: Callable[[str], Dict[str, str]] = _parser_gen(
    r"""
    ^Version:(?P<version>\d+.\d+|.\d+|\d+.)\s*
    StartHTML:(?P<start_html>\d+)\s*
    EndHTML:(?P<end_html>\d+)\s*
    StartFragment:(?P<start_fragment>\d+)\s*
    EndFragment:(?P<end_fragment>\d+)\s*
    (?:StartSelection:(?P<start_selection>\d+)\s*
    EndSelection:(?P<end_selection>\d+))?\s*
    (?:SourceURL:(?P<source_url>.*?)\s*$)?\s*
    (?P<html>(?:.|\s)*)
    """
)


def _get_html(content: Literal["fragment", "select", "html", "raw"] = "html") -> str:
    data = _get_clipboard(ClipboardFormat.HTML).decode('utf-8').strip('\x00')
    parse = _parse_html(data)
    try:
        match content:
            case "html":
                return data[int(parse['start_html']): int(parse['end_html'])]
            case "select":
                return data[int(parse['start_selection']): int(parse['end_selection'])]
            case "fragment":
                return data[int(parse['start_fragment']): int(parse['end_fragment'])]
            case "raw":
                return data
            case _:
                raise ValueError("Invalid content type")
    except AttributeError:
        raise ClipboardError("Content type does not exists")


@_clipboard
def _set_html(fragment: str, select: str | Tuple[int, int] = "", context: str = "",
              url: str = "file:///jqboard") -> None:
    try:
        if isinstance(select, str):
            select_start = fragment.index(select)
            select_end = select_start + len(select)
        else:
            select_start, select_end = select
    except (AttributeError, ValueError):
        raise ValueError("'select' argument is invalid. It should be a tuple or string that contained in fragment.")

    try:
        context = context or f"<html><body><!--StartFragment-->{fragment}<!--EndFragment--></body></html>"
        fragment_start = context.index(fragment)
        fragment_end = fragment_start + len(fragment)
    except ValueError:
        raise ValueError("'fragment' does not exists in context.")

    try:
        text = ''.join(etree.HTML(context).itertext())
    except:
        raise ValueError("illegal html content.")

    prefix_template = ("Version:1.0\r\n"
                       "StartHTML:%09d\r\n"
                       "EndHTML:%09d\r\n"
                       "StartFragment:%09d\r\n"
                       "EndFragment:%09d\r\n"
                       "StartSelection:%09d\r\n"
                       "EndSelection:%09d\r\n"
                       "SourceURL:%s\r\n")
    prefix = prefix_template % (0, 0, 0, 0, 0, 0, url)
    prefix_len = len(prefix)

    prefix = prefix_template % (
        prefix_len, prefix_len + len(context), prefix_len + fragment_start, prefix_len + fragment_end,
        prefix_len + select_start, prefix_len + select_end, url)

    data = prefix + context
    clip.EmptyClipboard()
    _set_clipboard(data.encode('utf-8'), ClipboardFormat.HTML)
    _set_clipboard(text, ClipboardFormat.TEXT)


@_clipboard
def _set_image(img: Image):
    clip.EmptyClipboard()
    with BytesIO() as data_buf:
        img.convert('RGB').save(data_buf, 'BMP')
        data = data_buf.getvalue()[14:]
    _set_clipboard(data, ClipboardFormat.IMAGE)


def _get_image() -> Image:
    data_buf = BytesIO()
    data_buf.write(_get_clipboard(ClipboardFormat.IMAGE))
    return Image.open(data_buf)


@_clipboard
def _set_text(text: str):
    clip.EmptyClipboard()
    if not isinstance(text, str):
        raise ValueError("Illegal argument 'text'. 'text' must be string.")
    _set_clipboard(text, ClipboardFormat.TEXT)


def _get_text() -> str:
    return _get_clipboard(ClipboardFormat.TEXT)


class WindowsClipboard(Clipboard):
    platform = Platform.WINDOWS

    def paste(self, fmt: ClipboardFormat = ClipboardFormat.TEXT,
              content: Literal['fragment', 'select', 'html', 'raw'] = "fragment") -> Any:
        match fmt:
            case ClipboardFormat.TEXT:
                return _get_text()
            case ClipboardFormat.HTML:
                return _get_html(content)
            case ClipboardFormat.IMAGE:
                return _get_image()

    def list(self) -> list[ClipboardFormat]:
        return [
            _INT_TO_FORMAT[fmt] for fmt in _get_formats()
            if fmt in _INT_TO_FORMAT
        ]

    def copy(self, data, fmt: ClipboardFormat = ...) -> None:
        if fmt is ...:
            fmt = guess_format(data)
        match fmt:
            case ClipboardFormat.TEXT:
                _set_text(data)
            case ClipboardFormat.HTML:
                _set_html(data)
            case ClipboardFormat.IMAGE:
                _set_image(data)
