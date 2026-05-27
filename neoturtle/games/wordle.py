
import discord
import random
import time

from data import Data
from ext.neoturtle.account import change_xp, earn_tokens
from neoturtle.gamesmanager import GamesManager
from neoturtle.wordsmanager import WordsManager
from utils.perms import get_missing_perms

Data = Data()
WordsManager = WordsManager()
GamesManager = GamesManager()

guess_cooldowns = {}

class GuessModal(discord.ui.Modal):
    def __init__(self, bot: discord.Bot):
        super().__init__(title=f"Wordle Guess")
        self.add_item(discord.ui.InputText(
            label=f"Input your guess:",
            placeholder="guess",
            min_length=5,
            max_length=5,
        ))

    async def callback(self, interaction: discord.Interaction):
        bot = interaction.client
        channel = interaction.channel
        # on cooldown
        last_guess = guess_cooldowns.get(channel.id, 0)
        remaining = 5 - (time.time() - last_guess)
        if remaining > 0:
            await interaction.response.send_message(f"Words are being guessed too quickly! Try again <t:{int(time.time() + remaining)}:R>", ephemeral=True)
            return
        guess = self.children[0].value.lower()
        # letters only
        if not guess.isalpha():
            await interaction.response.send_message(f"Guess `{guess}` is invalid! Guesses may only contain letters", ephemeral=True)
            return
        # word in dictionary
        if guess not in WordsManager.wordlists['dictionary']:
            await interaction.response.send_message(f"The word `{guess}` isn't in the dictionary!", ephemeral=True)
            return
        # wordle game active
        game_data = Data['neoturtle/channel'].get(channel.id, {}).get('playing')
        if not game_data or game_data['game'] != 'wordle' or (len(game_data['guesses']) >= 6):
            await interaction.response.send_message("There is no active Wordle game in this channel!", ephemeral=True)
            return
        # word already guessed
        if guess in game_data['guesses']:
            await interaction.response.send_message(f"Word `{guess}` has already been guessed!", ephemeral=True)
            return
        # word length check
        word = game_data['word']
        if not len(guess) == len(word):
            await interaction.response.send_message(f"Guess `{guess}` is invalid! Guesses must be {len(word)} letters long", ephemeral=True)
            return
        game_data['guesses'].append(guess)
        guess_cooldowns[channel.id] = time.time()
        msg = get_wordle_msg(bot, word, game_data['guesses'])
        guess_xp = 10
        total_xp = guess_xp
        if guess == word:
            reward = [100, 50, 25, 20, 15, 10][len(game_data['guesses']) - 1]
            earn_tokens(interaction.user, reward)
            xp = 50
            total_xp += xp - guess_xp
            Data['neoturtle/channel'][channel.id].pop('playing', None)
            embed = bot.newembed(description=f"### Solved in {len(game_data['guesses'])} by {interaction.user.mention}!\n+{bot.bot_emojis['token']}{reward}, +{xp}{bot.bot_emojis['xp']}\nAll participants earned {guess_xp}{bot.bot_emojis['xp']} per guess", color=discord.Color.green())
            response = {'content': msg, 'embed': embed}
        elif len(game_data['guesses']) >= 6:
            Data['neoturtle/channel'][channel.id].pop('playing', None)
            word_emojis = ''.join(get_wordle_emoji(bot, 'green', letter) for letter in word)
            embed = bot.newembed(description=f"### Game Over!\nThe word was {word_emojis}", color=discord.Color.red())
            response = {'content': msg, 'embed': embed}
        else:
            # build wordle keyboard
            keyboard = build_wordle_keyboard(bot, word, game_data['guesses'])
            embed = bot.newembed(description=f"{keyboard}", color=discord.Color.dark_green())
            response = {'content': msg, 'view': WordleView(bot), 'embed': embed}
        await change_xp(interaction.user, total_xp)
        try:
            msg = await channel.fetch_message(game_data['msg_id'])
            await msg.edit(content=response['content'], embed=response.get('embed'), view=response.get('view'), allowed_mentions=discord.AllowedMentions.none())
            await interaction.response.defer()
        except discord.HTTPException:
            sent = await interaction.response.send_message(**response, allowed_mentions=discord.AllowedMentions.none())
            sent = await sent.original_response()
            if Data['neoturtle/channel'].get(channel.id, {}).get('playing') and Data['neoturtle/channel'][channel.id]['playing']['game'] == 'wordle':
                Data['neoturtle/channel'][channel.id]['playing']['msg_id'] = sent.id

class GuessButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Enter Wordle Guess",
            style=discord.ButtonStyle.success,
            custom_id="wordle_guess_button",
        )
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(GuessModal(interaction.client))

class WordleView(discord.ui.View):
    def __init__(self, bot: discord.Bot):
        super().__init__(timeout=None)
        self.add_item(GuessButton())

def build_wordle_keyboard(bot: discord.Bot, word: str, guesses: list[str]) -> str:
    space_char = ' '
    keyboard = ['qwertyuiop', f'{space_char*3}asdfghjkl', f'{space_char*6}zxcvbnm']
    letter_status = {}
    for guess in guesses:
        for i, letter in enumerate(guess):
            if letter_status.get(letter) == 'green':
                continue
            if letter == word[i]:
                letter_status[letter] = 'green'
            elif letter in word:
                letter_status[letter] = 'yellow'
            else:
                letter_status[letter] = 'gray'
    rows = []
    for row in keyboard:
        rows.append(''.join(
            letter if letter == space_char else get_wordle_emoji(bot, letter_status.get(letter, 'light_gray'), letter)
            for letter in row
        ))
    return '\n'.join(rows)

def get_wordle_emoji(bot: discord.Bot, color: str, letter: str) -> str:
    letter = letter.lower()
    if color == 'green':
        return str(bot.bot_emojis[f"wordle_green_{letter}"])
    elif color == 'yellow':
        return str(bot.bot_emojis[f"wordle_yellow_{letter}"])
    elif color == 'gray':
        return str(bot.bot_emojis[f"wordle_gray_{letter}"])
    else:
        return str(bot.bot_emojis[f"wordle_light_gray_{letter}"])

def get_wordle_msg(bot: discord.Bot, word: str, guesses: list[str]) -> str:
    msg = ''
    for i in range(6):
        if i < len(guesses):
            guess = guesses[i]
            word_chars = list(word)
            colors = [get_wordle_emoji(bot, 'gray', guess[i]) for i in range(5)]
            # first pass: greens
            for i in range(5):
                if guess[i] == word_chars[i]:
                    colors[i] = get_wordle_emoji(bot, 'green', guess[i])
                    word_chars[i] = None
            # second pass: yellows
            for i in range(5):
                if colors[i] == get_wordle_emoji(bot, 'green', guess[i]):
                    continue
                if guess[i] in word_chars:
                    colors[i] = get_wordle_emoji(bot, 'yellow', guess[i])
                    word_chars[word_chars.index(guess[i])] = None
            msg += ''.join(colors) + '\n'
        else:
            msg += f"{str(bot.bot_emojis['wordle_empty']) * 5}\n"
    return msg

async def listen_game(bot, invoked_at, channel):
    bot.add_view(WordleView(bot))

async def start_game(bot: discord.Bot, channel: discord.TextChannel, ctx: discord.ApplicationContext = None):
    word = random.choice(WordsManager.wordlists['wordle/main']).lower()
    msg = get_wordle_msg(bot, word, [])
    if ctx:
        sent = await ctx.respond(msg, view=WordleView(bot))
        sent = await sent.original_response()
    else:
        sent = await channel.send(msg, view=WordleView(bot))
    invoked_at = time.time()
    Data['neoturtle/channel'].setdefault(channel.id, {})
    Data['neoturtle/channel'][channel.id]['playing'] = {'game': 'wordle', 'start': invoked_at, 'word': word, 'guesses': [], 'msg_id': sent.id}

def setup_game(play_group:discord.SlashCommandGroup, bot:discord.Bot):
    # Create command
    @play_group.command(name="wordle", description="Play Wordle")
    async def play_wordle_command(
        ctx:discord.ApplicationContext,
        ):
        if (ctx.guild and ctx.guild.me):
            # check missing perms
            required_perms = discord.Permissions(send_messages=True)
            missing_perms = get_missing_perms(ctx.channel, ctx.guild.me, required_perms)
            if missing_perms.value != 0:
                await GamesManager.no_permissions_prompt(ctx, missing_perms)
                return
        # Handle already playing a game in this channel
        if Data['neoturtle/channel'].get(ctx.channel_id, {}).get('playing'):
            game_data = Data['neoturtle/channel'][ctx.channel_id]['playing']
            # resend game msg
            if game_data['game'] == 'wordle':
                msg = get_wordle_msg(bot, game_data['word'], game_data['guesses'])
                if (len(game_data['guesses']) <= 0):
                    response = {'content': msg, 'view': WordleView(bot)}
                else:
                    keyboard = build_wordle_keyboard(bot, game_data['word'], game_data['guesses'])
                    embed = bot.newembed(description=f"{keyboard}", color=discord.Color.dark_green())
                    response = {'content': msg, 'view': WordleView(bot), 'embed': embed}
                sent = await ctx.respond(**response)
                Data['neoturtle/channel'][ctx.channel.id]['playing']['msg_id'] = sent.id
                return
            # cancel prompt
            await GamesManager.cancel_prompt(ctx, game_data['game'] or 'unknown')
            return
        await start_game(bot, ctx.channel, ctx)
