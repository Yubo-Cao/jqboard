from jqboard.clipboard import Clipboard, ClipboardFormat
from PIL import Image
from pathlib import Path

clip = Clipboard()
print(clip.paste(ClipboardFormat.TEXT))
print(clip.paste(ClipboardFormat.HTML))

with Image.open(Path(__file__).parent / "assets" / "picture.png") as img:
    clip.copy(img)
