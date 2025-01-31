
#  ------------------------------
#   < < < ChicknTurtle's Bots > > >
#     ------------------------------   

from os import chdir
from sys import stdout
import asyncio
from traceback import format_exc

from bots import Bots
from data import Data
from utils import Log, config, filepath

chdir(filepath)

config = config()

Log = Log()
Log.set_debug(config['log_debug'])

Data = Data()
Bots = Bots()

# Set terminal title
terminal_title = config['terminal_title']
if config['dev_mode']:
    terminal_title += ' DEV'
stdout.write(f"\033]0;{terminal_title}\007")
stdout.flush()

# Load extensions
from extensionloader import load_exts
for bot in Bots:
    load_exts(bot)

loop = asyncio.get_event_loop()

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
        Log.error(f"Error during task cancellation:\n{format_exc()}")

for bot in Bots:
    try:
        loop.run_until_complete(bot.on_quit())
        loop.run_until_complete(bot.close())
    except Exception as e:
        Log.error(f"Error during shutdown of bot {bot.name}:\n{format_exc()}")
loop.stop()

# Reset terminal title
stdout.write("\033]0;\007")
stdout.flush()

exit(1)
