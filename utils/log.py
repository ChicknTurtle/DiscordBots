
from colorama import Fore, Style
from datetime import datetime

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
