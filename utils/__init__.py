
from os import path, chdir
from yaml import safe_load

from utils.log import Log
from utils.images import load_image, rgb_split_image, attachment_to_image, image_to_bufferimg, stack_images_horizontally, overlay_center
from utils.numbers import format_time, format_time_short, format_number

# directory of project
filepath = path.dirname(path.dirname(path.abspath(__file__)))

def config():
    chdir(filepath)
    with open('config.yaml', 'r') as file:
        config = safe_load(file)
    return config
