
import discord

from data import Data
from utils import Log

Log = Log()
Data = Data()

class CancelButton(discord.ui.Button):
    def __init__(self, ctx, game):
        super().__init__(
            label = f"Cancel {game}",
            style = discord.ButtonStyle.primary,
        )
    async def callback(self, interaction:discord.Interaction):
        await GamesManager().cancel_game(interaction)

class CancelView(discord.ui.View):
    def __init__(self, ctx, game):
        super().__init__(timeout=None)
        self.add_item(CancelButton(ctx, game))

class GamesManager():
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    def _initialize(self):
        from neoturtle.gameloader import load_games
        self.games = load_games()
        
    async def cancel_game(self, ctx:discord.ApplicationContext):
        if Data['neoturtle/channel'].get(ctx.channel_id, {}).get('playing'):
            if (Data['neoturtle/channel'][ctx.channel_id]['playing']['permanent']
                and not isinstance(ctx.channel, discord.DMChannel)
                and not ctx.author.guild_permissions.manage_channels):
                await self.permanent_cancel_noperm_prompt(ctx)
                return
            await ctx.respond(f"Cancelled {Data['neoturtle/channel'][ctx.channel_id]['playing']['game']}.")
            Data['neoturtle/channel'][ctx.channel_id].pop('playing', None)
        else:
            await ctx.respond(f"There is no game to cancel in this channel!", ephemeral=True)
    
    async def use_hint(self, bot:discord.Bot, ctx:discord.ApplicationContext):
        if Data['neoturtle/channel'].get(ctx.channel_id, {}).get('playing'):
            game = Data['neoturtle/channel'][ctx.channel_id]['playing']['game']
            if self.games[game].get('use_hint'):
                await self.games[game]['use_hint'](bot, ctx)
            else:
                await ctx.respond("This game doesn't support hints.", ephemeral=True)
        else:
            await ctx.respond(f"There is no active game in this channel!", ephemeral=True)

    async def cancel_prompt(self, ctx:discord.ApplicationContext, game:str):
        await ctx.respond("A game is already being played in this channel!", view=CancelView(ctx, game), ephemeral=True)

    async def permanent_start_noperm_prompt(self, ctx:discord.ApplicationContext):
        await ctx.respond("You can't do that!\nYou must have Manage Channels permission to start a permanent game.", ephemeral=True)
    
    async def permanent_cancel_noperm_prompt(self, ctx:discord.ApplicationContext):
        await ctx.respond("You can't do that!\nYou must have Manage Channels permission to cancel a permanent game.", ephemeral=True)
    
    async def max_hints_prompt(self, ctx:discord.ApplicationContext):
        await ctx.respond("You have already used the max amount of hints.", ephemeral=True)
