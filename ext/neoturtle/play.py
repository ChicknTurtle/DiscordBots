
import os
import importlib
import time
import traceback
import discord

from data import Data
from utils import *

Data = Data()
Log = Log()

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

class GamesManager():
    def __init__(self, bot:discord.Bot):
        self.play_group = bot.create_group("play", "Play some games!")
        self.play_group.helpdesc = "Creating a permanent game in a channel requires Manage Channels permission."
        self.games = {} 
        for file_name in os.listdir('ext/neoturtle/games'):
            if file_name.endswith('.py'):
                game_name = os.path.splitext(file_name)[0]
                
                module_path = f"ext.neoturtle.games.{game_name}"
                
                try:
                    module = importlib.import_module(module_path)
                    self.games[game_name] = {
                        'listen': getattr(module, 'listen_game'),
                        'setup_game': getattr(module, 'setup_game')
                    }
                except Exception as e:
                    Log.error(f"Error loading game '{game_name}':\n{traceback.format_exc()}")

    async def cancel_prompt(self, ctx:discord.ApplicationContext):
        await ctx.respond("A game is already being played in this channel!", view=CancelView(), ephemeral=True)

def setup(bot:discord.Bot):
    games_manager = GamesManager(bot)

    # cancel
    @games_manager.play_group.command(name="cancel", description="Cancel the current game in this channel")
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
    
    for game in games_manager.games:
        games_manager.games[game]['setup_game'](games_manager, bot)
    
    # Continue games when bot restarts
    async def start_games():
        await bot.wait_until_ready()
        for channel_id, channel_data in Data['neoturtle/channel'].items():
            if channel_data.get('playing'):
                invoked_at = time.time()
                channel_data['playing']['start'] = invoked_at
                channel = await bot.fetch_channel(channel_id)
                bot.loop.create_task(games_manager.games[channel_data['playing']['game']]['listen'](bot, channel, invoked_at))
    bot.loop.create_task(start_games())
