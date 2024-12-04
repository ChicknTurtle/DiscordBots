
import time
import discord

from data import Data
from utils import *
from neoturtle.gamesmanager import GamesManager

Data = Data()
Log = Log()
GamesManager = GamesManager()

def setup(bot:discord.Bot):

    play_group = bot.create_group("play", "Play some games!")
    play_group.helpdesc = "Creating a permanent game in a channel requires Manage Channels permission."
    
    for game in GamesManager.games:
        GamesManager.games[game]['setup_game'](play_group, bot)

    # Cancel
    @play_group.command(name="cancel", description="Cancel the current game in this channel")
    async def play_cancel_command(ctx:discord.ApplicationContext):
        await GamesManager.cancel_game(ctx)
    
    # Hint
    @play_group.command(name="hint", description="Get a hint")
    async def play_hint_command(ctx:discord.ApplicationContext):
        await GamesManager.use_hint(bot, ctx)
    
    # Continue games when bot restarts
    async def start_games():
        await bot.wait_until_ready()
        for channel_id, channel_data in Data['neoturtle/channel'].items():
            if channel_data.get('playing'):
                invoked_at = time.time()
                channel_data['playing']['start'] = invoked_at
                channel = await bot.fetch_channel(channel_id)
                try:
                    game = GamesManager.games[channel_data['playing']['game']]
                    bot.loop.create_task(game['listen'](bot, channel, invoked_at))
                except KeyError:
                    Log.warn(f"Tried to continue an unknown game: {channel_data['playing']['game']} ({channel_id})")
    bot.loop.create_task(start_games())
