
import traceback
from datetime import datetime
import discord

from bots import Bots
from data import Data
from dev import handle_dev
from utils import Log, config, format_time

config = config()

Bots = Bots()
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
        Log.log(f"{bot.name} ready! Logged in as {bot.user.name}#{bot.user.discriminator} ({bot.user.id})")
        # Only load stuff once
        if bot.name == Bots[0].name:
            now = datetime.now()
            Data['global']['startTime'] = now
            try:
                downtime = format_time(now - Data['global']['stopTime'])
            except KeyError:
                downtime = 'unknown'
            await bot.get_channel(config['channels']['system']).send(f"Started! **Downtime**: {downtime}")
            if Data.get(f"{bot.name.lower()}/global"):
                Data[f"{bot.name.lower()}/global"].setdefault('commandsUsed', 0)
        # Load application emojis
        Log.debug(f"Loading application emojis for {bot.name}...")
        bot.app_emojis = await bot.fetch_application_emojis()
        Log.log(f"Loaded {len(bot.app_emojis)} application emojis for {bot.name}")
    
    async def on_quit():
        """Should be called before the bot is stopped."""
        if bot.name == Bots[0].name:
            now = datetime.now()
            Data['global']['stopTime'] = now
            Data.save()
            try:
                uptime = format_time(now - Data['global']['startTime'])
            except KeyError:
                uptime = 'unknown'
            await bot.get_channel(config['channels']['system']).send(f"Stopping. **Uptime**: {uptime}")
    bot.on_quit = on_quit
    
    # on message
    @bot.event
    async def on_message(msg:discord.Message):
        await handle_dev(bot, msg)

    # on message edit
    @bot.event
    async def on_message_edit(before:discord.Message, after:discord.Message):
        await handle_dev(bot, after)

    # on command
    @bot.event
    async def on_application_command(ctx:discord.ApplicationContext):
        Log.log(f"{bot.name} | @{ctx.author.name} used /{ctx.command}")
        await bot.get_channel(config['channels']['log']).send(f"<@{ctx.author.id}> used /{ctx.command}", allowed_mentions=discord.AllowedMentions.none())
        if Data.get(f"{bot.name.lower()}/global"):
            Data[f"{bot.name.lower()}/global"].setdefault('commandsUsed', 0)
            Data[f"{bot.name.lower()}/global"]['commandsUsed'] += 1
    
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
        await bot.get_channel(config['channels']['log']).send(f"**Joined**: {guildname} ({guild.member_count} members)", allowed_mentions=discord.AllowedMentions.none())
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
        await bot.get_channel(config['channels']['log']).send(f"**Left**: {guild.name} ({guild.member_count} members)", allowed_mentions=discord.AllowedMentions.none())
