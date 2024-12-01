
import random
import time
import json
import discord

from data import Data
from utils import *
from neoturtle.wordsmanager import WordsManager

Data = Data()
WordsManager = WordsManager()
config = config()

from ext.neoturtle.account import earn_tokens

def scramble(words:list[str]):
    scrambled = list(words[0])
    while True:
        random.shuffle(scrambled)
        scrambled_str = ''.join(scrambled)
        if scrambled_str not in words:
            return scrambled_str

# listen unscramble
async def listen_game(bot:discord.Bot, channel:discord.TextChannel, invoked_at:float):
    def check(m):
        return m.channel == channel
    while True:
        guess_msg = await bot.wait_for('message', check=check)
        # Stop if game isn't being played anymore
        game = Data['neoturtle/channel'].get(channel.id, {}).get('playing')
        if not game or game['start'] != invoked_at:
            break
        # Check if the guess is correct
        guess = guess_msg.content.strip().lower()
        if guess in Data['neoturtle/channel'][channel.id]['playing']['words']:
            reward = Data['neoturtle/channel'][channel.id]['playing']['reward']
            earn_tokens(guess_msg.author, reward)
            await channel.send(f"Correct! The word was **{guess}** +{bot.customemojis['neotoken2']}{reward}")
            permanent = Data['neoturtle/channel'][channel.id]['playing']['permanent']
            Data['neoturtle/channel'][channel.id].pop('playing', None)
            if permanent:
                await start_game(bot, channel, True)
            break

# start unscramble
async def start_game(bot:discord.Bot, channel:discord.TextChannel, permanent:bool, ctx:discord.ApplicationContext=None):
    # Choose word
    anagrams = WordsManager.anagrams['main']
    words = anagrams[random.choice(list(anagrams.keys()))]
    scrambled = scramble(words)
    # Choose reward
    reward = len(words[0])
    if random.random() > 0.99:
        reward = random.choice([25,50])
    if reward < 25:
        msg = f"Unscramble: **{scrambled}**"
    else:
        msg = f"Unscramble: **{scrambled}** :sparkles: {bot.customemojis['neotoken2']}{reward}"
    if config['dev_mode']:
        msg += f" ||{'/'.join(words)}||"
    if ctx:
        await ctx.respond(msg)
    else:
        await channel.send(msg)
    # Create game
    invoked_at = time.time()
    Data['neoturtle/channel'].setdefault(channel.id, {})
    Data['neoturtle/channel'][channel.id]['playing'] = {'game':'unscramble','start':invoked_at,'permanent':permanent,'words':words,'scrambled':scrambled,'reward':reward}
    # Listen for correct guess
    await listen_game(bot, channel, invoked_at)

def setup_game(games_manager, bot:discord.Bot):
    # create command
    @games_manager.play_group.command(name="unscramble", description="Unscramble words")
    async def play_unscramble_command(ctx:discord.ApplicationContext, permanent:str=discord.Option(description="Requires Manage Channels permission", choices=['True', 'False'], default='False')):
        permanent = True if permanent == 'True' else False
        if permanent:
            if not ctx.author.guild_permissions.manage_channels:
                await ctx.respond("You can't do that!\nYou must have Manage Channels permission to start a permanent game.", ephemeral=True)
                return
        if Data['neoturtle/channel'].get(ctx.channel_id, {}).get('playing'):
            if Data['neoturtle/channel'][ctx.channel_id]['playing']['game'] == 'unscramble':
                reward = Data['neoturtle/channel'][ctx.channel_id]['playing']['reward']
                scrambled = Data['neoturtle/channel'][ctx.channel_id]['playing']['scrambled']
                if reward < 25:
                    msg = f"Unscramble: **{scrambled}**"
                else:
                    msg = f"Unscramble: **{scrambled}** :sparkles: {bot.customemojis['neotoken2']}{reward}"
                await ctx.respond(msg)
            else:
                await games_manager.cancel_prompt()
            return
        await start_game(bot, ctx.channel, permanent, ctx)
