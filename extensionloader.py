
import traceback
import discord

from utils import *

Log = Log()

def loadext(bot:discord.Bot, files:list):
    for file in files:
        try:
            bot.load_extension(f"ext.{file}")
        except Exception as e:
            Log.error(f"Failed to load extension: 'ext.{file}' for {bot.name}")
            Log.error(traceback.format_exc())

    Log.log(f"Loaded extensions for {bot.name}.")
