
import asyncio
import random
import time
import math
import discord
import emoji
import re

from data import Data
from utils import Log, config
from neoturtle.gamesmanager import GamesManager
from neoturtle.wordsmanager import WordsManager

Log = Log()
Data = Data()
WordsManager = WordsManager()
GamesManager = GamesManager()
config = config()

from ext.neoturtle.account import earn_tokens, change_xp

BOLD_UNDERLINE = "\033[1m\033[4m"
RESET_BOLD_UNDERLINE = "\033[22m\033[24m"

def scramble(words:list[str], attempts:int=100) -> str:
    scrambled = list(words[0])
    for _ in range(attempts):
        random.shuffle(scrambled)
        result = ''.join(scrambled)
        if result not in words:
            return result
    Log.warn(f"Failed to scrambled word {'/'.join(words)} after {attempts} attempts")
    return random.choice(words)

def scramble_hint(words:list[str], level:int=1, attempts:int=100) -> str:
    word_length = len(words[0])
    fixed_positions = {0}
    hint_amount = max(1,min(word_length-2,(word_length-1)/4))
    while len(fixed_positions) < math.ceil(hint_amount*level):
        fixed_positions.add(random.randint(1, word_length - 1))
    success = False
    for _ in range(attempts):
        scrambled = list(words[0])
        unfixed_indices = [i for i in range(word_length) if i not in fixed_positions]
        random.shuffle(unfixed_indices)
        temp_word = [words[0][i] for i in unfixed_indices]
        random.shuffle(temp_word)
        for i, new_pos in zip(unfixed_indices, temp_word):
            scrambled[i] = new_pos
        if ''.join(scrambled) not in words:
            success = True
            break
    result = []
    debug_result = []
    i = 0
    while i < word_length:
        if i in fixed_positions:
            start = i
            while i + 1 < word_length and i + 1 in fixed_positions:
                i += 1
            result.append(f"**__{''.join(words[0][start:i+1])}__**")
            debug_result.append(f"{BOLD_UNDERLINE}{''.join(words[0][start:i+1])}{RESET_BOLD_UNDERLINE}")
        else:
            result.append(scrambled[i])
            debug_result.append(scrambled[i])
        i += 1
    if not success:
        Log.warn(f"Failed to scramble hint for {'/'.join(words)} after {attempts} attempts: {''.join(debug_result)}")
    return ''.join(result)

def format_guess(guess:str) -> str:
    guess = guess.strip().lower()
    # allow emojis to work
    match = re.match(r"<a?:([a-zA-Z0-9_]+):\d+>", guess)
    if match:
        guess = match.group(1)
    guess = emoji.demojize(guess, language='alias')
    if guess.startswith(':') and guess.endswith(':'):
        guess = guess[1:-1]
    return guess

# Listen unscramble
async def listen_game(bot:discord.Bot, channel:discord.TextChannel, invoked_at:float):
    def check(msg:discord.Message):
        game = Data['neoturtle/channel'].get(channel.id, {}).get('playing')
        # pass check if game isn't being played anymore so we can stop listening
        if not game or game['start'] != invoked_at:
            return True
        if msg.channel.id != channel.id:
            return False
        # check if the guess is correct
        guess = format_guess(msg.content)
        words = Data['neoturtle/channel'][channel.id]['playing']['words']
        return guess in words
    while True:
        guess_msg = await bot.wait_for_message_or_edit(check)
        # Stop if game isn't being played anymore
        game = Data['neoturtle/channel'].get(channel.id, {}).get('playing')
        if not game or game['start'] != invoked_at:
            break
        guess = format_guess(guess_msg.content)
        words = Data['neoturtle/channel'][channel.id]['playing']['words']
        reward = Data['neoturtle/channel'][channel.id]['playing']['reward']
        Data['neoturtle/channel'][channel.id]['playing']['rewardmult'] = Data['neoturtle/channel'][channel.id]['playing'].setdefault('rewardmult',1)
        rewardmult = Data['neoturtle/channel'][channel.id]['playing']['rewardmult']
        actual_reward = math.ceil(reward*rewardmult)
        earn_tokens(guess_msg.author, actual_reward)
        xp = 10
        change_xp(guess_msg.author, xp)
        real_word = f" ({words[0]})" if guess != words[0] else ''
        await channel.send(f"Correct! The word was **{guess}**{real_word} +{bot.customemojis['neotoken2']}{actual_reward}, {xp}xᴘ")
        permanent = Data['neoturtle/channel'][channel.id]['playing']['permanent']
        Data['neoturtle/channel'][channel.id].pop('playing', None)
        if permanent:
            await start_game(bot, channel, True)
        break

# Start unscramble
async def start_game(bot:discord.Bot, channel:discord.TextChannel, permanent:bool, ctx:discord.ApplicationContext=None):
    # Choose word
    anagrams = WordsManager.anagrams['main']
    words = anagrams[random.choice(list(anagrams.keys()))]
    loop = asyncio.get_running_loop()
    scrambled = await loop.run_in_executor(None, scramble, words)
    hint1 = await loop.run_in_executor(None, scramble_hint, words, 1)
    hint2 = await loop.run_in_executor(None, scramble_hint, words, 2)
    # Choose reward
    reward = len(words[0])
    bonus = False
    if random.random() > 0.99:
        reward = random.choice([25,50])
        bonus = True
    if bonus:
        msg = f"Unscramble: {scrambled} :sparkles:"
    else:
        msg = f"Unscramble: {scrambled}"
    if config['dev_mode']:
        msg += f" ||{'/'.join(words)}||"
    if ctx:
        await ctx.respond(msg)
    else:
        await channel.send(msg)
    # Create game
    invoked_at = time.time()
    Data['neoturtle/channel'].setdefault(channel.id, {})
    Data['neoturtle/channel'][channel.id]['playing'] = {'game':'unscramble','start':invoked_at,'permanent':permanent,'words':words,'scrambled':scrambled,'hint1':hint1,'hint2':hint2,'reward':reward,'rewardmult':1,'bonus':bonus,'hints':0}
    # Listen for correct guess
    await listen_game(bot, channel, invoked_at)

# Use hint
async def use_hint(bot:discord.Bot, ctx:discord.ApplicationContext=None):
    scrambled = Data['neoturtle/channel'][ctx.channel_id]['playing']['scrambled']
    bonus = Data['neoturtle/channel'][ctx.channel_id]['playing']['bonus']
    # Increase hints
    hints = Data['neoturtle/channel'][ctx.channel_id]['playing']['hints']
    if hints >= 2:
        await GamesManager.max_hints_prompt(ctx)
        return
    hints += 1
    Data['neoturtle/channel'][ctx.channel_id]['playing']['hints'] = hints
    shown_word = Data['neoturtle/channel'][ctx.channel_id]['playing'].get(f'hint{hints}',scrambled)
    # Lower reward
    Data['neoturtle/channel'][ctx.channel_id]['playing']['rewardmult'] = Data['neoturtle/channel'][ctx.channel_id]['playing'].setdefault('rewardmult',1)
    Data['neoturtle/channel'][ctx.channel_id]['playing']['rewardmult'] /= 2
    rewardmult = Data['neoturtle/channel'][ctx.channel_id]['playing']['rewardmult']
    if bonus:
        msg = f"Unscramble: {shown_word} :sparkles: ({bot.customemojis['neotoken2']}{100*rewardmult}%)"
    else:
        msg = f"Unscramble: {shown_word} ({bot.customemojis['neotoken2']}{int(100*rewardmult)}%)"
    await ctx.respond(msg)

def setup_game(play_group:discord.SlashCommandGroup, bot:discord.Bot):
    # Create command
    @play_group.command(name="unscramble", description="Unscramble words")
    async def play_unscramble_command(
        ctx:discord.ApplicationContext,
        permanent=discord.Option(bool, default=False, description="Requires Manage Channels permission"),
        ):
        if (permanent
            and not isinstance(ctx.channel, discord.DMChannel)
            and not ctx.author.guild_permissions.manage_channels):
            await GamesManager.permanent_start_noperm_prompt(ctx)
            return
        # Handle already playing a game in this channel
        if Data['neoturtle/channel'].get(ctx.channel_id, {}).get('playing'):
            if Data['neoturtle/channel'][ctx.channel_id]['playing']['game'] == 'unscramble':
                rewardmult = Data['neoturtle/channel'][ctx.channel_id]['playing'].setdefault('rewardmult',1)
                hints = Data['neoturtle/channel'][ctx.channel_id]['playing']['hints']
                bonus = Data['neoturtle/channel'][ctx.channel_id]['playing']['bonus']
                scrambled = Data['neoturtle/channel'][ctx.channel_id]['playing']['scrambled']
                shown_word = Data['neoturtle/channel'][ctx.channel_id]['playing'].get(f'hint{hints}',scrambled)
                if bonus:
                    msg = f"Unscramble: {shown_word} :sparkles:"
                else:
                    msg = f"Unscramble: {shown_word}"
                    msg += f" ({bot.customemojis['neotoken2']}{int(100*rewardmult)}%)" if rewardmult != 1 else ""
                await ctx.respond(msg)
            else:
                await GamesManager.cancel_prompt(ctx, Data['neoturtle/channel'][ctx.channel_id]['playing']['game'])
            return
        await start_game(bot, ctx.channel, permanent, ctx)
