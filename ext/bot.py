
import time
import math
import discord
from discord.ext import commands

from data import Data
from utils import Log, config, format_number

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
        server_count = format_number(len(bot.guilds))
        member_count = format_number(len(bot.users))
        commands_used = format_number(Data.get(f"{bot.name.lower()}/global", {}).get('commandsUsed', 0))
        if discord.IntegrationType.user_install in bot.default_command_integration_types:
            invite_url = f"https://discord.com/oauth2/authorize?client_id={bot.user.id}"
        else:
            invite_url = f"https://discord.com/oauth2/authorize?client_id={bot.user.id}&scope=applications.commands%20bot"
        msg = [f"## {bot.name} Statistics"]
        msg.append(f":ping_pong: Ping: `{ping}ms`")
        msg.append(f":stopwatch: Bot started <t:{uptime}:R>")
        msg.append(f":homes: {server_count} servers")
        msg.append(f":busts_in_silhouette: {member_count} members")
        msg.append(f":robot: {commands_used} commands used")
        msg.append(f":incoming_envelope: [Add {bot.name} to My Apps or Server](<{invite_url}>)")
        await ctx.respond('\n'.join(msg), ephemeral=True)
    
    # suggest
    @bot_group.command(name="suggest", description="Suggest a feature for the bot")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def bot_suggest_command(ctx:discord.ApplicationContext, suggestion:str=discord.Option(str, "Your feedback", max_length=1000)):
        suggestion_quote = '\n'.join('> '+line for line in suggestion.splitlines())
        await bot.get_channel(config['channels']['feedback']).send(f"<@{ctx.author.id}> sent a suggestion:\n{suggestion_quote}", allowed_mentions=discord.AllowedMentions.none())
        await ctx.author.send(f"Your suggestion was received:\n{suggestion_quote}\n-# You can send another suggestion <t:{math.ceil(time.time()+300)}:R>", allowed_mentions=discord.AllowedMentions.none())
        await ctx.respond(f"Suggestion sent successfully! :rocket:", ephemeral=True)
    bot_suggest_command.helpdesc = "Max limit of 1000 characters and 5m cooldown"
    # suggest error
    @bot_suggest_command.error
    async def bot_suggest_command_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            cooldowntime = math.ceil(time.time()+error.retry_after)
            await ctx.respond(f"You're on cooldown to avoid spamming.\nTry again <t:{cooldowntime}:R>", ephemeral=True)
        else:
            raise error
