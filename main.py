
#  ------------------------------
#   < < < ChicknTurtle's Bots > > >
#     ------------------------------   

import os
import sys
import asyncio
import traceback

from bots import Bots
from data import Data
from utils import *

os.chdir(filepath)

config = config()

Log = Log()
Log.set_debug(config['log_debug'])

Data = Data()
Bots = Bots()

# Load extensions
from extensionloader import loadext
for bot in Bots:
    ext_key = f"ext_{bot.name.lower()}"
    exts = config.get(ext_key)
    if exts:
        loadext(bot, exts)
    else:
        Log.warn(f"No extensions found for bot '{bot.name}'")

loop = asyncio.get_event_loop()

# Set terminal title
sys.stdout.write(f"\033]0;{config['terminal_title']}\007")
sys.stdout.flush()

# Run the bots
for bot in Bots:
    loop.create_task(bot.start(bot.token))

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    # Cancel all tasks
    Log.log("Shutting down tasks...")
    tasks = asyncio.all_tasks(loop)
    for task in tasks:
        task.cancel()
    try:
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    except Exception as e:
        Log.error(f"Error during task cancellation:\n{traceback.format_exc()}")

for bot in Bots:
    try:
        loop.run_until_complete(bot.on_quit())
        loop.run_until_complete(bot.close())
    except Exception as e:
        Log.error(f"Error during shutdown of bot {bot.name}:\n{traceback.format_exc()}")
loop.stop()

# Reset terminal title
sys.stdout.write("\033]0;\007")
sys.stdout.flush()

exit(1)
