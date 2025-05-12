
from PIL import Image, ImageOps, UnidentifiedImageError, ImageDraw, ImageFilter
import numpy as np
import io
import discord
import requests
import os

def load_image(url:str) -> Image.Image:
    os.makedirs('cache', exist_ok=True)
    filename = os.path.join('cache', url.split('/')[-1])
    # load from cache
    if os.path.exists(filename):
        return Image.open(filename)
    # download image
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to download image: {url}")
    with open(filename, 'wb') as f:
        f.write(response.content)
    return Image.open(io.BytesIO(response.content))

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

def fill_block(block, data, axis, cmyk):
	# Mapping: (offset, channel, color_index)
	channels = [(0, 0, 0), (1, 1, 1), (2, 2, 2)] if not cmyk else [
		(0, 1, 1), (1, 2, 2), (2, 0, 0),  # green, blue, red
		(0, 2, 2), (1, 0, 0), (2, 1, 1)   # magenta, yellow, cyan
	]
	for offset, channel, color_index in channels:
		tiled = np.tile(data[:, color_index].reshape(-1, 1), (1, 3)) if axis == 0 else np.tile(data[:, color_index], (3, 1))
		if axis == 0:
			block[offset::3, :, channel] = tiled
		else:
			block[:, offset::3, channel] = tiled
	# alpha
	alpha = np.tile(data[:, 3].reshape(-1, 1), (1, 3)) if axis == 0 else np.tile(data[:, 3], (3, 1))
	if axis == 0:
		block[0::3, :, 3] = block[1::3, :, 3] = block[2::3, :, 3] = alpha
	else:
		block[:, 0::3, 3] = block[:, 1::3, 3] = block[:, 2::3, 3] = alpha

def rgb_split_image(img:Image.Image, cmyk:bool=False, horizontal:bool=False) -> Image.Image:
    # config
    main_size = 64
    # scale input down if over these dimensions
    max_width = main_size
    max_height = main_size
    # scale output image up if under these dimensions
    min_width = main_size * 8
    min_height = main_size * 8

    img = ImageOps.exif_transpose(img).convert('RGBA')
    width, height = img.size
    
    # scale down image
    if width > max_width or height > max_height:
        scale = min(max_width / width, max_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        width, height = img.size
    
    original = np.array(img)
    result = Image.new('RGBA', (width*3, height*3))
    
    # build effect
    if horizontal:
        for x in range(width):
            block = np.zeros((height * 3, 3, 4), dtype=np.uint8)
            column = original[:, x, :]
            fill_block(block, column, axis=0, cmyk=cmyk)
            block_img = Image.fromarray(block)
            result.paste(block_img, (x * 3, 0), block_img)
    else:
        for y in range(height):
            block = np.zeros((3, width * 3, 4), dtype=np.uint8)
            row = original[y, :, :]
            fill_block(block, row, axis=1, cmyk=cmyk)
            block_img = Image.fromarray(block)
            result.paste(block_img, (0, y * 3), block_img)
    
    # scale up final image
    scale_factor = 1
    while (width * 3 * scale_factor < min_width and height * 3 * scale_factor < min_height):
        scale_factor *= 2
    
    if scale_factor > 1:
        scaled_width = width * 3 * scale_factor
        scaled_height = height * 3 * scale_factor
        result = result.resize((scaled_width, scaled_height), Image.NEAREST)
    
    return result

def stack_images_horizontally(images:list[Image.Image], gap:int=0) -> Image.Image:
    if not images:
        raise ValueError("The list of images is empty.")
    max_height = max(img.height for img in images)
    total_width = sum(img.width for img in images) + gap * (len(images) - 1)
    combined = Image.new("RGBA", (total_width, max_height), (0, 0, 0, 0))
    current_x = 0
    for img in images:
        y_offset = (max_height - img.height) // 2
        combined.paste(img, (current_x, y_offset))
        current_x += img.width + gap    
    return combined

def overlay_center(bg_img:Image.Image, overlay_img:Image.Image, overlay_scale:float=1.0, shadow:float=0.0) -> Image.Image:
    target_height = int(bg_img.height * overlay_scale)
    overlay_aspect = overlay_img.width / overlay_img.height
    target_width = int(target_height * overlay_aspect)
    if target_width > bg_img.width:
        target_width = bg_img.width
        target_height = int(target_width / overlay_aspect)
    resized_overlay = overlay_img.resize((target_width, target_height), Image.LANCZOS)
    combined = bg_img.copy()
    x = (bg_img.width - target_width) // 2
    y = (bg_img.height - target_height) // 2
    if shadow:
        shadow_offset = int(target_height * shadow * 0.1)
        shadow_radius = int(target_height * shadow * 0.1)
        overlay_alpha = resized_overlay.convert("L")
        shadow_img = Image.new("RGBA", resized_overlay.size, (0, 0, 0, 255))
        shadow_img.putalpha(overlay_alpha)
        shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=shadow_radius))
        combined.paste(shadow_img, (x + shadow_offset, y + shadow_offset), shadow_img)
    combined.paste(resized_overlay, (x, y), resized_overlay.convert("RGBA"))
    return combined
