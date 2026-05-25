
import discord
import math

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

def get_level(xp:int):
    base = 100
    rate = 1.1
    if xp <= 0:
        return 1, 0, base
    real_level = math.log((xp * (rate - 1) / base) + 1, rate)
    lvl = math.floor(real_level) + 1
    start_xp = sum(int(base * (rate ** i)) for i in range(lvl - 1))
    end_xp = start_xp + int(base * (rate ** (lvl - 1)))
    return lvl, start_xp, end_xp

def get_lvlbar(bot, xp:int):
    lvl, start_xp, end_xp = get_level(xp)
    digits = ''.join(str(bot.bot_emojis[f"lvlbar_digit{digit}"]) for digit in str(lvl))
    segments = 8
    frac = max(0,min(1, (xp - start_xp) / (end_xp - start_xp)))
    total_units = segments*4
    filled_units = frac*total_units
    bar = []
    for i in range(segments):
        this_units = min(4,max(0, round(filled_units - i*4)))
        if this_units == 4 and filled_units > (i+1)*4:
            this_units = 5
        if i == 0:
            key = f"lvlbar_start{this_units}"
        elif i == segments - 1:
            key = f"lvlbar_end{this_units}"
        else:
            key = f"lvlbar_mid{this_units}"
        bar.append(str(bot.bot_emojis[key]))
    return f"{''.join(bar)} {digits}"

def setup(bot:discord.Bot):
    # profile
    @bot.command(name="profile", description="View your NeoTurtle profile")
    async def profile_command(ctx:discord.ApplicationContext, user=discord.Option(discord.User, required=False, description="View another user's profile")):
        user = ctx.author if user is None else user
        user = await bot.fetch_user(user.id) # fetch for accent color
        setup_user(user)
        tokens = Data['neoturtle/user'][user.id]['tokens']
        earned_tokens = Data['neoturtle/user'][user.id]['tokens-earned']
        xp = Data['neoturtle/user'][user.id]['xp']
        tokens = format_number(tokens)
        earned_tokens = format_number(earned_tokens)
        xp_str = format_number(xp)
        lvlbar = get_lvlbar(bot, xp)
        s = "'" if user.display_name.endswith('s') else "'s"
        embed = bot.newembed(title=f"{user.display_name}{s} Profile", description=f"{lvlbar}\n-# {xp_str}xp\nBalance: {bot.bot_emojis['token']}{tokens}\n{bot.bot_emojis['token']}{earned_tokens} earned total", color=user.accent_color or bot.color)
        embed.set_thumbnail(url=user.display_avatar.url)
        await ctx.respond(embed=embed, ephemeral=True)

    # achievements
    @bot.command(name="achievements", description="View your achievements")
    async def achievements_command(ctx:discord.ApplicationContext):
        await ctx.respond("achievements", ephemeral=True)
