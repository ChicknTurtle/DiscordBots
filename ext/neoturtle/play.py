
import random
import time
import discord

from data import Data
from utils import *
from ext.neoturtle.account import earn_tokens

Data = Data()
Log = Log()

def scramble(words:list[str]):
    scrambled = list(words[0])
    while True:
        random.shuffle(scrambled)
        scrambled_str = ''.join(scrambled)
        if scrambled_str not in words:
            return scrambled_str

class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label = "Cancel and start",
            style = discord.ButtonStyle.primary,
        )
    async def callback(self, interaction:discord.Interaction):
        await interaction.response.send_message("cancel button wip", ephemeral=True)

class CancelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CancelButton())

def setup(bot:discord.Bot):

    bot_group = bot.create_group("play", "Play some games!")
    bot_group.helpdesc = "Creating a permanent game in a channel requires Manage Channels permission."

    # Load anagram word groups
    anagram_word_groups = []
    with open("assets/wordlists/unscramble/main.txt", "r") as file:
        for line in file.readlines():
            words = line.strip().split(',')
            anagram_word_groups.append(words)
    # Load wordle words
    wordle_words = []
    with open("assets/wordlists/wordle/main.txt", "r") as file:
        for line in file.readlines():
            if len(line) == 5:
                wordle_words.append(line)

    # cancel
    @bot_group.command(name="cancel", description="Cancel the current game in this channel")
    async def play_cancel_command(ctx:discord.ApplicationContext):
        if Data['neoturtle/channel'].get(ctx.channel_id, {}).get('playing'):
            if Data['neoturtle/channel'][ctx.channel_id]['playing']['permanent'] is True:
                if not ctx.author.guild_permissions.manage_channels:
                    await ctx.respond("You can't do that!\nYou must have Manage Channels permission to cancel a permanent game.", ephemeral=True)
                    return
            await ctx.respond(f"Cancelled {Data['neoturtle/channel'][ctx.channel_id]['playing']['game']}.")
            Data['neoturtle/channel'][ctx.channel_id].pop('playing', None)
        else:
            await ctx.respond(f"There is no game to cancel in this channel!", ephemeral=True)

    # listen unscramble
    async def listen_unscramble(channel, invoked_at:float):
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
                    await start_unscramble(channel, True)
                break
    
    # start unscramble
    async def start_unscramble(channel:discord.abc.GuildChannel, permanent:bool, ctx:discord.ApplicationContext=None):
        # Choose word
        words = random.choice(anagram_word_groups)
        scrambled = scramble(words)
        # Choose reward
        reward = len(words[0])
        if random.random() > 0.99:
            reward = random.choice([25,50])
        if reward < 25:
            msg = f"Unscramble: **{scrambled}**"
        else:
            msg = f"Unscramble: **{scrambled}** :sparkles: {bot.customemojis['neotoken2']}{reward}"
        if ctx:
            await ctx.respond(msg)
        else:
            await channel.send(msg)
        # Create game
        invoked_at = time.time()
        Data['neoturtle/channel'].setdefault(channel.id, {})
        Data['neoturtle/channel'][channel.id]['playing'] = {'game':'unscramble','start':invoked_at,'permanent':permanent,'words':words,'scrambled':scrambled,'reward':reward}
        # Listen for correct guess
        await listen_unscramble(channel, invoked_at)

    # unscramble
    @bot_group.command(name="unscramble", description="Unscramble words")
    async def play_unscramble_command(ctx:discord.ApplicationContext,
                                      permanent:str=discord.Option(description="Requires Manage Channels permission", choices=['True', 'False'], default='False')):
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
                await ctx.respond(f"{msg} ||{'/'.join(Data['neoturtle/channel'][ctx.channel_id]['playing']['words'])}||")
            else:
                await ctx.respond("A game is already being played in this channel!", view=CancelView(), ephemeral=True)
            return
        await start_unscramble(ctx.channel, permanent, ctx)

    # listen wordle
    async def listen_wordle(channel, invoked_at:float):
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
            if guess == Data['neoturtle/channel'][channel.id]['playing']['word']:
                reward = Data['neoturtle/channel'][channel.id]['playing']['reward']
                earn_tokens(guess_msg.author, reward)
                await channel.send(f"You guess it! The word was **{guess}** +{bot.customemojis['neotoken2']}{reward}")
                permanent = Data['neoturtle/channel'][channel.id]['playing']['permanent']
                Data['neoturtle/channel'][channel.id].pop('playing', None)
                if permanent:
                    await start_unscramble(channel, True)
                break

    # start wordle
    async def start_wordle(channel:discord.abc.GuildChannel, permanent:bool, ctx:discord.ApplicationContext=None):
        # Choose word
        word = random.choice(wordle_words)
        # Choose reward
        reward = 15
        if random.random() > 0.99:
            reward = random.choice([50,75])
        e = ':black_large_square:'
        if reward < 50:
            msg = f"**Wordle**\n{e}{e}{e}{e}{e}"
        else:
            msg = f"**Wordle** :sparkles: {bot.customemojis['neotoken2']}{reward}\n{e}{e}{e}{e}{e}"
        if ctx:
            await ctx.respond(msg)
        else:
            await channel.send(msg)
        # Create game
        invoked_at = time.time()
        Data['neoturtle/channel'].setdefault(channel.id, {})
        Data['neoturtle/channel'][channel.id]['playing'] = {'game':'wordle','start':invoked_at,'permanent':permanent,'word':word,'guesses':[],'reward':reward}
        # Listen for correct guess
        await listen_wordle(channel, invoked_at)
    
    # wordle
    @bot_group.command(name="wordle", description="Wordle")
    async def play_wordle_command(ctx:discord.ApplicationContext,
                                      permanent:str=discord.Option(description="Requires Manage Channels permission", choices=['True', 'False'], default='False')):
        permanent = True if permanent == 'True' else False
        if permanent:
            if not ctx.author.guild_permissions.manage_channels:
                await ctx.respond("You can't do that!\nYou must have Manage Channels permission to start a permanent game.", ephemeral=True)
                return
        if Data['neoturtle/channel'].get(ctx.channel_id, {}).get('playing'):
            await ctx.respond("A game is already being played in this channel!", view=CancelView(), ephemeral=True)
            return
        await start_wordle(ctx.channel, permanent, ctx)
    
    # Continue games when bot restarts
    async def start_games():
        await bot.wait_until_ready()
        for channel_id, channel_data in Data['neoturtle/channel'].items():
            if channel_data.get('playing'):
                invoked_at = time.time()
                channel_data['playing']['start'] = invoked_at
                channel = await bot.fetch_channel(channel_id)
                if channel_data['playing']['game'] == 'unscramble':
                    await listen_unscramble(channel, invoked_at)
    bot.loop.create_task(start_games())
