
import discord

from data import Data
from utils import *

Data = Data()
Log = Log()

def setup_user(user:discord.User):
    Data['neoturtle/user'].setdefault(user.id, {})
    Data['neoturtle/user'][user.id].setdefault('tokens', 0)
    Data['neoturtle/user'][user.id].setdefault('tokens-earned', 0)
    Data['neoturtle/user'][user.id].setdefault('achievements', {})

def change_tokens(user:discord.User, amount:int):
    Data['neoturtle/user'][user.id]['tokens'] += amount

def earn_tokens(user:discord.User, amount:int):
    change_tokens(user,amount)
    Data['neoturtle/user'][user.id]['tokens-earned'] += amount

def setup(bot:discord.Bot):

    # profile
    @bot.command(name="profile", description="View your NeoTurtle profile")
    async def profile_command(ctx:discord.ApplicationContext):
        setup_user(ctx.author)
        tokens = Data['neoturtle/user'][ctx.author.id]['tokens']
        earned_tokens = Data['neoturtle/user'][ctx.author.id]['tokens-earned']
        tokens = format_number(tokens)
        earned_tokens = format_number(earned_tokens)
        await ctx.respond(f"{ctx.author.display_name}'s Profile\n{bot.customemojis['neotoken2']}{tokens}\n{bot.customemojis['neotoken2']}{earned_tokens} earned total", ephemeral=True)

    # achievements
    @bot.command(name="achievements", description="View your achievements")
    async def achievements_command(ctx:discord.ApplicationContext):
        await ctx.respond("achievements", ephemeral=True)
