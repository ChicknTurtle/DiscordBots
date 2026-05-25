
#  ------------------------------
#   < < < ChicknTurtle's Bots > > >
#     ------------------------------   

from os import chdir
import sys
import asyncio
import aiohttp
from traceback import format_exc

from utils import Log, Config, filepath
chdir(filepath)

from bots import Bots
from data import Data

config = Config()
config['dev_mode'] = '--dev' in sys.argv
config['log_debug'] = '--debug' in sys.argv

Log = Log()
Log.set_debug(config['log_debug'])

Data = Data()
Bots = Bots()

# Set terminal title
terminal_title = config['terminal_title']
if config['dev_mode']:
    terminal_title += ' DEV'
sys.stdout.write(f"\033]0;{terminal_title}\007")
sys.stdout.flush()

async def run_bot(bot):
    try:
        async with bot:
            try:
                await bot.start(bot.token)
            finally:
                await bot.on_quit()
    except aiohttp.client_exceptions.ClientConnectionResetError:
        Log.error(f"Ignoring ClientConnectionResetError for bot {bot.name}")
    except asyncio.CancelledError:
        raise
    except Exception:
        Log.error(f"Unexpected error in {bot.name}'s run bot loop:\n{format_exc()}")

async def main():
    async with asyncio.TaskGroup() as tg:
        if Data._autosave:
            tg.create_task(Data._autosave())
        for bot in Bots:
            tg.create_task(run_bot(bot))

try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass

# Reset terminal title
sys.stdout.write("\033]0;\007")
sys.stdout.flush()

exit(1)
