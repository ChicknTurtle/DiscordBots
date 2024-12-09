
import time
from datetime import datetime
import discord
from discord.ext import commands

from data import Data
from utils import *

config = config()

Log = Log()
Data = Data()

def setup(bot:discord.Bot):
    
    bot_group = bot.create_group("bot", "Bot information.")

    # stats
    @bot_group.command(name="stats", description="View interesting bot statistics")
    async def bot_stats_command(ctx:discord.ApplicationContext):
        ping = round(bot.latency*1000)
        uptime = round(Data['global']['startTime'].timestamp())
        servers = format_number(len(bot.guilds))
        users = format_number(len(bot.users))
        commands_used = format_number(Data[f"{bot.name.lower()}/global"]['commandsUsed'])
        invite_url = f"https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=applications.commands%20bot"
        (msg := []).append(f"## {bot.name} Statistics")
        msg.append(f":ping_pong: Ping: `{ping}ms`")
        msg.append(f":stopwatch: Bot started <t:{uptime}:R>")
        msg.append(f":homes: {servers} servers")
        msg.append(f":busts_in_silhouette: {users} users")
        msg.append(f":robot: {commands_used} commands used")
        msg.append(f":incoming_envelope: [Invite {bot.name} to your server](<{invite_url}>)")
        await ctx.respond('\n'.join(msg), ephemeral=True)
    
    # suggest
    @bot_group.command(name="suggest", description="Suggest a feature for the bot")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def bot_suggest_command(ctx:discord.ApplicationContext, suggestion:str=discord.Option(str, "Your suggestion", max_length=1000)):
        await bot.get_channel(config['channels']['feedback']).send(f"<@{ctx.author.id}> sent a suggestion:\n> {suggestion}", allowed_mentions=discord.AllowedMentions.none())
        await ctx.respond(f"Suggestion sent successfully! :rocket:", ephemeral=True)
    bot_suggest_command.helpdesc = "Max limit of 1000 characters"
    # suggest error
    @bot_suggest_command.error
    async def bot_suggest_command_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            cooldowntime = math.ceil(time.time()+error.retry_after)
            await ctx.respond(f"You're on cooldown! Try again <t:{cooldowntime}:R>.", ephemeral=True)
        else:
            raise error
