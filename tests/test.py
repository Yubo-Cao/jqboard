from jqboard.clipboard import Clipboard, ClipboardFormat
from PIL import Image

clip = Clipboard()
print(clip.paste(ClipboardFormat.TEXT))
print(clip.paste(ClipboardFormat.HTML))

with Image.open('./assets/picture.png') as img:
    clip.copy(img)
