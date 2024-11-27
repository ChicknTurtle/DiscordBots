
import pickle
import asyncio

from utils import *

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
        self._data['ids'] = {
            'owner': 957464464507166750,
            'devguild': 985362099490390096,
            'system': 991049580634308688,
            'log': 991110356908908704,
            'feedback': 1243661131961077861,
        }
        self._files = ['global','neoturtle/channel','neoturtle/user']
        for filename in self._files:
            with open(f'data/{filename}.db', 'rb') as file:
                try:
                    self._data[filename] = pickle.load(file)
                except EOFError:
                    self._data[filename] = {}
                    Log.warn(f"No data to load! ({filename})")
        Log.log("Loaded data.")
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
            with open(f'data/{filename}.db', 'wb') as file:
                pickle.dump(self._data[filename], file)
        if autosave:
            Log.debug("Autosaved data.")
        else:
            Log.log("Saved data.")
