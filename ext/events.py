
import traceback
from datetime import datetime
import discord

from data import Data
from dev import handle_dev
from utils import *

Log = Log()
Data = Data()

def setup(bot:discord.Bot):

    # on error
    async def on_error(event:str, *args, **kwargs):
        Log.error(f"Error in {event}:")
        Log.error(traceback.format_exc())
    bot.on_error = on_error

    # on connect
    @bot.event
    async def on_connect():
        Log.debug(f"{bot.name} connected to discord.")
        await bot.sync_commands()

    # on disconnect
    @bot.event
    async def on_disconnect():
        Log.debug(f"{bot.name} disconnected from discord...")

    # on ready
    @bot.listen(once=True)
    async def on_ready():
        Log.log(f"{bot.name} started!")
        if bot.name == "TuttleBot":
            now = datetime.now()
            Data['global']['startTime'] = now
            try:
                downtime = format_time(now - Data['global']['stopTime'])
            except KeyError:
                downtime = 'unknown'
            await bot.get_channel(Data['ids']['system']).send(f"Started! **Downtime**: {downtime}")
    
    async def on_quit():
        """Should be called before the bot is stopped."""
        if bot.name == "TuttleBot":
            now = datetime.now()
            Data['global']['stopTime'] = now
            Data.save()
            try:
                uptime = format_time(now - Data['global']['startTime'])
            except KeyError:
                uptime = 'unknown'
            await bot.get_channel(Data['ids']['system']).send(f"Stopping. **Uptime**: {uptime}")
    bot.on_quit = on_quit
    
    # on message
    @bot.event
    async def on_message(msg:discord.Message):
        await handle_dev(bot, msg)

    # on command
    @bot.event
    async def on_application_command(ctx:discord.ApplicationContext):
        Log.log(f"{bot.name} | {ctx.author.display_name} used /{ctx.command}")
        await bot.get_channel(Data['ids']['log']).send(f"<@{ctx.author.id}> used /{ctx.command}", allowed_mentions=discord.AllowedMentions.none())
    
    # on join
    @bot.event
    async def on_guild_join(guild:discord.Guild):
        invite = None
        if 'VANITY_URL' in guild.features:
            invite = (await guild.vanity_invite()).url
        if invite:
            guildname = f"[{guild.name}]({invite})"
        else:
            guildname = guild.name
        Log.log(f"{bot.name} joined: {guild.name} ({guild.member_count} members)")
        await bot.get_channel(Data['ids']['log']).send(f"**Joined**: {guildname} ({guild.member_count} members)", allowed_mentions=discord.AllowedMentions.none())
        # Welcome message
        if guild.system_channel:
            try:
                with open(f"assets/messages/{bot.name.lower()}-welcome.txt", 'r') as file:
                    welcome_msg = file.read()
                await guild.system_channel.send(welcome_msg)
            except FileNotFoundError:
                pass

    # on leave
    @bot.event
    async def on_guild_remove(guild:discord.Guild):
        Log.log(f"{bot.name} left: {guild.name} ({guild.member_count} members)")
        await bot.get_channel(Data['ids']['log']).send(f"**Left**: {guild.name} ({guild.member_count} members)", allowed_mentions=discord.AllowedMentions.none())
