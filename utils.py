
from colorama import Fore, Style
from datetime import datetime, timedelta
import os
import math
import yaml

class Log:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.log_debug = False
        Log.log(self, "Log initialized.")
    
    def set_debug(self, enabled:bool=True):
        self.log_debug = enabled

    def log(self, message:str):
        current_time = datetime.now().strftime("[%H:%M:%S]")
        print(f"{Fore.LIGHTBLACK_EX}{current_time}{Style.RESET_ALL} {Fore.GREEN}{message}{Style.RESET_ALL}")

    def error(self, message:str):
        current_time = datetime.now().strftime("[%H:%M:%S]")
        print(f"{Fore.LIGHTBLACK_EX}{current_time}{Style.RESET_ALL} {Fore.RED}{message}{Style.RESET_ALL}")

    def warn(self, message:str):
        current_time = datetime.now().strftime("[%H:%M:%S]")
        print(f"{Fore.LIGHTBLACK_EX}{current_time}{Style.RESET_ALL} {Fore.YELLOW}{message}{Style.RESET_ALL}")

    def debug(self, message:str):
        if self.log_debug:
            current_time = datetime.now().strftime("[%H:%M:%S]")
            print(f"{Fore.LIGHTBLACK_EX}{current_time}{Style.RESET_ALL} {Fore.CYAN}{message}{Style.RESET_ALL}")

# directory of this file
filepath = os.path.dirname(os.path.abspath(__file__))

def config():
    os.chdir(filepath)
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    return config

def format_time(delta:timedelta):
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    seconds =  round(seconds + delta.microseconds / 1e6, 2)
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
			value = math.floor(value * 10) / 10
			num = f"{value:.1f}"
			num = num.removesuffix('.0')
			return f"{sign}{num}{letter}"
	return f"{sign}{num}{letter}"
