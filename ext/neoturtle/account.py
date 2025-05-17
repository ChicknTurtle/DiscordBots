
import discord

from data import Data
from utils import Log, format_number

Data = Data()
Log = Log()

def setup_user(user:discord.User):
    Data['neoturtle/user'].setdefault(user.id, {})
    Data['neoturtle/user'][user.id].setdefault('tokens', 0)
    Data['neoturtle/user'][user.id].setdefault('tokens-earned', 0)
    Data['neoturtle/user'][user.id].setdefault('xp', 0)
    Data['neoturtle/user'][user.id].setdefault('achievements', {})

def change_tokens(user:discord.User, amount:int):
    setup_user(user)
    Data['neoturtle/user'][user.id]['tokens'] += amount

def change_xp(user:discord.User, amount:int):
    setup_user(user)
    Data['neoturtle/user'][user.id]['xp'] += amount

def earn_tokens(user:discord.User, amount:int):
    change_tokens(user,amount)
    Data['neoturtle/user'][user.id]['tokens-earned'] += amount

def setup(bot:discord.Bot):
    # profile
    @bot.command(name="profile", description="View your NeoTurtle profile")
    async def profile_command(ctx:discord.ApplicationContext, user=discord.Option(discord.User, required=False, description="View another user's profile")):
        user = ctx.author if user is None else user
        setup_user(user)
        tokens = Data['neoturtle/user'][user.id]['tokens']
        earned_tokens = Data['neoturtle/user'][user.id]['tokens-earned']
        xp = Data['neoturtle/user'][user.id]['xp']
        tokens = format_number(tokens)
        earned_tokens = format_number(earned_tokens)
        xp = format_number(xp)
        s = "'" if user.display_name.endswith('s') else "'s"
        await ctx.respond(f"## {user.display_name}{s} Profile\n{xp} xᴘ\nBalance: {bot.app_emojis['token']}{tokens}\n{bot.app_emojis['token']}{earned_tokens} earned total", ephemeral=True)

    # achievements
    @bot.command(name="achievements", description="View your achievements")
    async def achievements_command(ctx:discord.ApplicationContext):
        await ctx.respond("achievements", ephemeral=True)
