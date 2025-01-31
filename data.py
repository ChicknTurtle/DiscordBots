
import os
import pickle
import asyncio

from utils import Log, config

Log = Log()
config = config()

class Data:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self._data = {}
        self._files = ['global','tuttlebot/global','neoturtle/global','neoturtle/channel','neoturtle/user']
        for filename in self._files:
            filepath = f'data/{filename}.db'
            # Create file if it doesn't exist
            if not os.path.exists(filepath):
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'wb') as file:
                    pickle.dump({}, file)
                Log.warn(f"Data file didn't exist! ({filename})")
            # Load file
            with open(filepath, 'rb') as file:
                try:
                    self._data[filename] = pickle.load(file)
                except EOFError:
                    self._data[filename] = {}
                    Log.warn(f"Loaded empty data file! ({filename})")
        Log.log("Loaded data.")
        # Start autosaving
        if config['autosave_time'] != 0:
            async def autosave():
                while True:
                    await asyncio.sleep(config['autosave_time'])
                    self.save(autosave=True)
            loop = asyncio.get_event_loop()
            loop.create_task(autosave())
        
    
    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __iter__(self):
        return iter([self])
    
    def save(self, autosave=False):
        for filename in self._files:
            filepath = f'data/{filename}.db'
            with open(filepath, 'wb') as file:
                pickle.dump(self._data[filename], file)
        if autosave:
            Log.debug("Autosaved data.")
        else:
            Log.log("Saved data.")
