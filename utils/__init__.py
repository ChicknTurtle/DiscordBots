
from datetime import timedelta
from os import path, chdir
from math import floor
from yaml import safe_load

from utils.log import Log

# directory of project
filepath = path.dirname(path.dirname(path.abspath(__file__)))

def config():
    chdir(filepath)
    with open('config.yaml', 'r') as file:
        config = safe_load(file)
    return config

def format_time(delta:timedelta):
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    seconds = round(seconds + delta.microseconds / 1e6, 2)
    parts = []
    if days:
        parts.append(f"{days} {'day' if days == 1 else 'days'}")
    if hours:
        parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
    if minutes:
        parts.append(f"{minutes} {'minute' if minutes == 1 else 'minutes'}")
    if seconds:
        parts.append(f"{seconds} {'second' if seconds == 1 else 'seconds'}")
    return ', '.join(parts)

def format_number(num:int) -> str:
	letters = ["", "k", "M", "B", "T"]
	sign = '-' if num < 0 else ''
	num = abs(num)
	if num == 0:
		return '0'
	for i, letter in enumerate(letters):
		unit = 1000 ** i
		if num < unit * 1000:
			value = num / unit
			value = floor(value * 10) / 10
			num = f"{value:.1f}"
			num = num.removesuffix('.0')
			return f"{sign}{num}{letter}"
	return f"{sign}{num}{letter}"
