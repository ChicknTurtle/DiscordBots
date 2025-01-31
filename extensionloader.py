
import traceback
import discord

from utils import Log, config

config = config()

Log = Log()

def load_exts(bot:discord.Bot):
    ext_key = f"ext_{bot.name.lower()}"
    exts:list = config.get(ext_key)
    exts.append(bot.name.lower())
    if exts:
        for ext in exts:
            try:
                bot.load_extension(f"ext.{ext}")
            except Exception as e:
                Log.error(f"Failed to load extension: 'ext.{ext}' for {bot.name}")
                Log.error(traceback.format_exc())
        Log.log(f"Loaded extensions for {bot.name}.")
    else:
        Log.warn(f"No extensions found for bot '{bot.name}'")
