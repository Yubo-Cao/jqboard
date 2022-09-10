import logging

from jqboard.clipboard import ClipboardFormat

logger = logging.getLogger(__name__)


class ClipboardError(Exception):
    """Base class for exceptions in this module."""

    def __init__(self, message):
        self.message = message
        logger.error(message)


class ClipboardEmpty(ClipboardError):
    """Raised when the clipboard is empty."""

    def __init__(self):
        super().__init__("The clipboard is empty.")

    def __str__(self):
        return f'{self.__class__}: {self.message}'


class ClipboardNotText(ClipboardError):
    """Raised when the clipboard is not text."""

    def __init__(self):
        super().__init__("The clipboard is not text.")


class ClipboardNotImage(ClipboardError):
    """Raised when the clipboard is not an image."""

    def __init__(self):
        super().__init__("The clipboard is not an image.")


class ClipboardNotHTML(ClipboardError):
    """Raised when the clipboard is not HTML."""

    def __init__(self):
        super().__init__("The clipboard is not HTML.")


def raise_format_error(fmt: ClipboardFormat) -> None:
    match fmt:
        case ClipboardFormat.TEXT:
            raise ClipboardNotText()
        case ClipboardFormat.IMAGE:
            raise ClipboardNotImage()
        case ClipboardFormat.HTML:
            raise ClipboardNotHTML()
