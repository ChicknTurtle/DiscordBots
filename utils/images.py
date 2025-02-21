
from PIL import Image, ImageOps, UnidentifiedImageError
import numpy as np
import io
import discord

def image_to_bufferimg(img:Image.Image) -> io.BytesIO:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

async def attachment_to_image(attach:discord.Attachment) -> Image.Image|None:
    try:
        if not attach.content_type.startswith('image/'):
            return None
        data = await attach.read()
        return Image.open(io.BytesIO(data))
    except UnidentifiedImageError:
        return None

def rgb_split_image(img: Image.Image) -> Image.Image:
    # config
    main_size = 64
    # scale input down if over these dimensions
    max_width = main_size
    max_height = main_size
    # scale output image up if under these dimensions
    min_width = main_size * 8
    min_height = main_size * 8

    img = ImageOps.exif_transpose(img).convert('RGBA')  # Use RGBA to handle transparency
    width, height = img.size
    
    # scale down image
    if width > max_width or height > max_height:
        scale = min(max_width / width, max_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        width, height = img.size
    
    original = np.array(img)
    result = Image.new('RGBA', (width * 3, height * 3))
    
    # build effect
    for y in range(height):
        block = np.zeros((3, width * 3, 4), dtype=np.uint8)
        row = original[y, :, :]
        
        block[:, 0::3, 0] = np.tile(row[:, 0], (3, 1))  # red
        block[:, 1::3, 1] = np.tile(row[:, 1], (3, 1))  # green
        block[:, 2::3, 2] = np.tile(row[:, 2], (3, 1))  # blue
        block[:, 0::3, 3] = np.tile(row[:, 3], (3, 1))  # alpha red
        block[:, 1::3, 3] = np.tile(row[:, 3], (3, 1))  # alpha green
        block[:, 2::3, 3] = np.tile(row[:, 3], (3, 1))  # alpha blue
        
        block_img = Image.fromarray(block)
        result.paste(block_img, (0, y * 3), block_img)  # Use alpha channel as mask for pasting
    
    # scale up final image
    scale_factor = 1
    while (width * 3 * scale_factor < min_width and height * 3 * scale_factor < min_height):
        scale_factor *= 2
    
    if scale_factor > 1:
        scaled_width = width * 3 * scale_factor
        scaled_height = height * 3 * scale_factor
        result = result.resize((scaled_width, scaled_height), Image.NEAREST)
    
    return result
