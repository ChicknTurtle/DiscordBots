
from datetime import datetime
import discord

from data import Data
from utils import *

config = config()

Log = Log()
Data = Data()

class InviteButton(discord.ui.Button):
    def __init__(self, bot:discord.Bot):
        options = []
        for command in bot.commands:
            if command.name != 'help':
                options.append(discord.SelectOption(label=command.name, value=command.name))

        super().__init__(
            label = "Add App",
            style = discord.ButtonStyle.link,
            url = f"https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=applications.commands%20bot"
        )

class InviteView(discord.ui.View):
    def __init__(self, bot:discord.Bot):
        self.bot = bot
        super().__init__(timeout=None)
        self.add_item(InviteButton(self.bot))

def setup(bot:discord.Bot):
    
    bot_group = bot.create_group("bot", "Bot information.")

    # ping
    @bot_group.command(name="ping", description="Get the bot's latency")
    async def bot_ping_command(ctx:discord.ApplicationContext):
        ping = round(bot.latency*1000)
        await ctx.respond(f":ping_pong: **Pong!** `{ping}ms`")

    # uptime
    @bot_group.command(name="uptime", description="Get the bot's uptime")
    async def bot_uptime_command(ctx:discord.ApplicationContext):
        startTime = Data['global']['startTime']
        uptime = format_time(datetime.now() - startTime)
        await ctx.respond(f":stopwatch: **Bot started <t:{round(startTime.timestamp())}:R>**")

    # invite
    @bot_group.command(name="invite", description="Invite the bot to your server")
    async def bot_invite_command(ctx:discord.ApplicationContext):
        view = InviteView(bot)
        await ctx.respond(f"Click the button below to invite {bot.name} to your server:", view=view)
    
    # suggest
    @bot_group.command(name="suggest", description="Suggest a feature for the bot")
    async def bot_suggest_command(ctx:discord.ApplicationContext, suggestion:str=discord.Option(str, "Your suggestion", max_length=1000)):
        await bot.get_channel(config['channels']['feedback']).send(f"<@{ctx.author.id}> sent a suggestion:\n> {suggestion}")
        await ctx.respond(f"Suggestion sent successfully! :rocket:", ephemeral=True)
    bot_suggest_command.helpdesc = "Max limit of 1000 characters"
