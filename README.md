# `jqboard`

`jqboard` is a platform independent implementation to handle clipboard for Linux & Windows. Mac OS is not supported.
It allows copy, paste of the following format:

- `PIL.Image` Image
- `text/plain` Text'
- `text/html` HTML

In addition, this library is very pythonic and easy to use.

## Requirements

- Python 3.10+
- Pillow
- Lxml
- Pywin32 (Windows only)
- Xclip or Wl-clipboard (Linux only), depending on desktop environment

## Installation

```bash
pip install jqboard
```

## Example

```python
from jqboard.clipboard import Clipboard, ClipboardFormat
from jqboard.error import ClipboardError
from PIL import Image

clip = Clipboard()
print(clip.paste(ClipboardFormat.TEXT))  # HTML, IMAGE

try:
    clip.copy("Hello World") # smart format detection
    clip.copy("<h1>Hello World</h1>")
    clip.copy(Image.open("tests/assets/picture.png"))
except ClipboardError as e:
    print(e)
```
