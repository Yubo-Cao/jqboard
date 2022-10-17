from abc import abstractmethod, ABC
from enum import Enum
from typing import Any, Dict, Literal, Type
import platform


class ClipboardFormat(Enum):
    TEXT = "text"
    IMAGE = "image"
    HTML = "html"


class Platform(Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"

    @classmethod
    def current(cls) -> "Platform":
        if getattr(cls, "_current", None) is None:
            cls._current = Platform(platform.system().lower())
        return cls._current


class Clipboard(ABC):
    """
    Abstract class for clipboard
    """

    _clip: str = ""

    def __new__(cls, *args, **kwargs) -> "Clipboard":
        if cls is Clipboard:
            plat = Platform.current()
            if plat == Platform.WINDOWS:
                from jqboard.win_clipboard import WindowsClipboard

                cls = WindowsClipboard
            elif plat == Platform.LINUX:
                from jqboard.linux_clipboard import LinuxClipboard

                cls = LinuxClipboard
            else:
                raise NotImplementedError("Unsupported platform")
        return super().__new__(cls)

    def __init__(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def copy(self, data, fmt: ClipboardFormat = ...) -> None:
        """
        Copy data to clipboard
        """
        raise NotImplementedError

    @abstractmethod
    def paste(self, fmt: ClipboardFormat = ClipboardFormat.TEXT) -> Any:
        """
        Paste data from clipboard
        """
        raise NotImplementedError

    @abstractmethod
    def list(self) -> list[ClipboardFormat]:
        """
        List formats supported by clipboard
        """
        raise NotImplementedError
