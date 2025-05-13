
import random
import time
import math
import discord

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

def scramble(word:str) -> str:
    scrambled = list(word)
    attempts = 0
    while attempts < 100:
        random.shuffle(scrambled)
        result = ''.join(scrambled)
        if result != word:
            return result
        attempts += 1
    else:
        #Log.warn(f"Failed to scrambled word {word} after {attempts} attempts")
        return word

def scramble_hint(word:str, hint_amount:float=0.5) -> str:
    word_length = len(word)
    fixed_positions = {0}
    num_fixed = max(1, int(word_length * hint_amount))
    while len(fixed_positions) < num_fixed:
        fixed_positions.add(random.randint(1, word_length - 1))
    original_word = word
    attempts = 0
    while attempts < 100:
        scrambled = list(word)
        unfixed_indices = [i for i in range(word_length) if i not in fixed_positions]
        random.shuffle(unfixed_indices)
        temp_word = [word[i] for i in unfixed_indices]
        random.shuffle(temp_word)
        for i, new_pos in zip(unfixed_indices, temp_word):
            scrambled[i] = new_pos
        if ''.join(scrambled) != original_word:
            break
        attempts += 1
    else:
        #Log.warn(f"Failed to scrambled word {original_word} after {attempts} attempts")
        pass
    result = []
    i = 0
    while i < word_length:
        if i in fixed_positions:
            start = i
            while i + 1 < word_length and i + 1 in fixed_positions:
                i += 1
            result.append(f"**__{''.join(word[start:i + 1])}__**")
        else:
            result.append(scrambled[i])
        i += 1
    return ''.join(result)

# Listen unscramble
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
            xp = 10
            change_xp(guess_msg.author, xp)
            await channel.send(f"Correct! The word was **{guess}** +{bot.customemojis['neotoken2']}{reward}, {xp}xᴘ")
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
    scrambled = scramble(words[0])
    hint = scramble_hint(words[0], 0.5)
    hint2 = scramble_hint(words[0], 0.75)
    # Choose reward
    reward = len(words[0])
    bonus = False
    if random.random() > 0.99:
        reward = random.choice([25,50])
        bonus = True
    if reward < 25:
        msg = f"Unscramble: {scrambled}"
    else:
        msg = f"Unscramble: {scrambled} :sparkles: {bot.customemojis['neotoken2']}{reward}"
    if config['dev_mode']:
        msg += f" ||{'/'.join(words)}||"
    if ctx:
        await ctx.respond(msg)
    else:
        await channel.send(msg)
    # Create game
    invoked_at = time.time()
    Data['neoturtle/channel'].setdefault(channel.id, {})
    Data['neoturtle/channel'][channel.id]['playing'] = {'game':'unscramble','start':invoked_at,'permanent':permanent,'words':words,'scrambled':scrambled,'hint':hint,'hint2':hint2,'reward':reward,'bonus':bonus,'hints':0}
    # Listen for correct guess
    await listen_game(bot, channel, invoked_at)

# Use hint
async def use_hint(bot:discord.Bot, ctx:discord.ApplicationContext=None):
    Data['neoturtle/channel'][ctx.channel_id]['playing']['hints'] += 1
    hints = Data['neoturtle/channel'][ctx.channel_id]['playing']['hints']
    if hints >= 3:
        await GamesManager.max_hints_prompt(ctx)
        return
    if hints < 2:
        hint = Data['neoturtle/channel'][ctx.channel_id]['playing']['hint']
    else:
        hint = Data['neoturtle/channel'][ctx.channel_id]['playing']['hint2']
    # Lower reward
    reward = Data['neoturtle/channel'][ctx.channel_id]['playing']['reward']
    Data['neoturtle/channel'][ctx.channel_id]['playing']['reward'] = math.ceil(reward / 2)
    reward = Data['neoturtle/channel'][ctx.channel_id]['playing']['reward']
    bonus = Data['neoturtle/channel'][ctx.channel_id]['playing']['bonus']
    if bonus == False:
        msg = f"Unscramble: {hint} {bot.customemojis['neotoken2']}{reward}"
    else:
        msg = f"Unscramble: {hint} :sparkles: {bot.customemojis['neotoken2']}{reward}"
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
                reward = Data['neoturtle/channel'][ctx.channel_id]['playing']['reward']
                bonus = Data['neoturtle/channel'][ctx.channel_id]['playing']['bonus']
                scrambled = Data['neoturtle/channel'][ctx.channel_id]['playing']['scrambled']
                if bonus == False:
                    msg = f"Unscramble: {scrambled}"
                else:
                    msg = f"Unscramble: {scrambled} :sparkles: {bot.customemojis['neotoken2']}{reward}"
                await ctx.respond(msg)
            else:
                await GamesManager.cancel_prompt(ctx, Data['neoturtle/channel'][ctx.channel_id]['playing']['game'])
            return
        await start_game(bot, ctx.channel, permanent, ctx)
