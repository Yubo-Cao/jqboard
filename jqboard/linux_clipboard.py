import os
import subprocess
from abc import ABC
from io import BytesIO
from typing import Any, cast

from PIL import Image

from clipboard import ClipboardFormat, Clipboard, Platform
from jqboard.error import raise_format_error, ClipboardError

_FORMAT_TO_STR = {
    ClipboardFormat.TEXT: "text/plain",
    ClipboardFormat.HTML: "text/html",
    ClipboardFormat.IMAGE: "image/png",
}
_STR_TO_FORMAT = {v: k for k, v in _FORMAT_TO_STR.items()}


def _format_output(data: bytes, fmt: ClipboardFormat) -> Any:
    match fmt:
        case ClipboardFormat.TEXT | ClipboardFormat.HTML:
            return data.decode("utf-8")
        case ClipboardFormat.IMAGE:
            return Image.open(BytesIO(data))


def _format_input(data: Any, fmt: ClipboardFormat) -> bytes:
    match fmt:
        case ClipboardFormat.TEXT | ClipboardFormat.HTML:
            return data.encode("utf-8")
        case ClipboardFormat.IMAGE:
            cast(Image.Image, data).save(buf := BytesIO(), "PNG")
            return buf.getvalue()


class WaylandClipboard(Clipboard):
    def copy(self, data, fmt: ClipboardFormat = ClipboardFormat.TEXT) -> None:
        try:
            subprocess.run(["wl-copy", "-t", _FORMAT_TO_STR[fmt]], input=_format_input(data, fmt), check=True)
        except subprocess.CalledProcessError as e:
            raise ClipboardError("Failed to copy to clipboard") from e

    def paste(self, fmt: ClipboardFormat = ClipboardFormat.TEXT) -> Any:
        if fmt not in self.list():
            raise_format_error(fmt)
        try:
            data = subprocess.run(["wl-paste", "-t", _FORMAT_TO_STR[fmt]], capture_output=True, check=True,
                                  stdout=subprocess.PIPE).stdout
            return _format_output(data, fmt)
        except subprocess.CalledProcessError as e:
            raise ClipboardError("Failed to paste from clipboard") from e

    def list(self) -> list[ClipboardFormat]:
        try:
            fmts = (subprocess.check_output(["wl-paste", "-l"], text=True)
                    .strip()
                    .split("\n"))
            return [_STR_TO_FORMAT[fmt] for fmt in fmts if fmt in _STR_TO_FORMAT]
        except subprocess.CalledProcessError as e:
            raise ClipboardError("Failed to list formats") from e


class X11Clipboard(Clipboard):
    def list(self):
        try:
            fmts = (subprocess.check_output(["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"], text=True)
                    .strip()
                    .split("\n"))
            return [_STR_TO_FORMAT[fmt] for fmt in fmts if fmt in _STR_TO_FORMAT]
        except subprocess.CalledProcessError as e:
            raise ClipboardError("Failed to list formats") from e

    def copy(self, data, fmt: ClipboardFormat = ClipboardFormat.TEXT) -> None:
        try:
            subprocess.run(["xclip", "-selection", "clipboard", "-t", _FORMAT_TO_STR[fmt]],
                           input=_format_input(data, fmt),
                           check=True)
        except subprocess.CalledProcessError as e:
            raise ClipboardError("Failed to copy to clipboard") from e

    def paste(self, fmt: ClipboardFormat = ClipboardFormat.TEXT) -> Any:
        if fmt not in self.list():
            raise_format_error(fmt)
        try:
            data = subprocess.run(["xclip", "-selection", "clipboard", "-t", _FORMAT_TO_STR[fmt], "-o"],
                                  capture_output=True, check=True, stdout=subprocess.PIPE)
            return _format_output(data.stdout, fmt)
        except subprocess.CalledProcessError as e:
            raise ClipboardError("Failed to paste from clipboard") from e


class LinuxClipboard(Clipboard, ABC):
    platform = Platform.LINUX

    def __new__(cls, *args, **kwargs):
        if os.environ.get("XDG_SESSION_TYPE", None) == "wayland" or os.environ.get("WAYLAND_DISPLAY", None):
            return WaylandClipboard()
        else:
            return X11Clipboard()
