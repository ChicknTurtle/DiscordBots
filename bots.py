
import aiohttp
import asyncio
import discord
from dotenv import load_dotenv
import os

from utils import Log

Log = Log()

load_dotenv(dotenv_path='tokens.env')

class Bots:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self._bots = []

        intents = discord.Intents.all()
        intents.presences = False

        self.tuttlebot = discord.AutoShardedBot(intents=intents, help_command=None, default_command_integration_types={discord.IntegrationType.guild_install,discord.IntegrationType.user_install})
        self.tuttlebot.name = "TuttleBot"
        self.tuttlebot.token = os.getenv('tuttlebot')
        self.tuttlebot.color = 0x309c58
        if self.tuttlebot.token:
            self._bots.append(self.tuttlebot)

        self.neoturtle = discord.AutoShardedBot(intents=intents, help_command=None, default_command_integration_types={discord.IntegrationType.guild_install,discord.IntegrationType.user_install})
        self.neoturtle.name = "NeoTurtle"
        self.neoturtle.token = os.getenv('neoturtle')
        self.neoturtle.color = 0x00ff00
        if self.neoturtle.token:
            self._bots.append(self.neoturtle)
        
        self.splatdrone = discord.AutoShardedBot(intents=intents, help_command=None, default_command_integration_types={discord.IntegrationType.guild_install,discord.IntegrationType.user_install})
        self.splatdrone.name = "Splatdrone"
        self.splatdrone.token = os.getenv('splatdrone')
        self.splatdrone.color = 0x00b4ff
        if self.splatdrone.token:
            self._bots.append(self.splatdrone)

        for bot in self:
            bot.newembed = self.newembed_wrapper(bot)
            bot.wait_for_message_or_edit = self.wait_for_message_or_edit_wrapper(bot)
            bot.fetch_application_emojis = self.fetch_application_emojis_wrapper(bot)
    
    def __iter__(self):
        return iter(self._bots)
    
    def __getitem__(self, index):
        return self._bots[index]
        
    def newembed_wrapper(self, bot:discord.Bot):
        def newembed(title:str='', description:str='', footer:str=None, color:discord.Color=None, fields:list[tuple]=[], **kwargs):
            if color is None:
                color = bot.color
            embed = discord.Embed(title=title, description=description, color=color, **kwargs)
            embed.set_footer(text=footer)
            for field in fields:
                name, value, inline = (field+(None, None, None))[:3]
                embed.add_field(name=name, value=value, inline=inline)
            return embed
        return newembed

    def wait_for_message_or_edit_wrapper(self, bot:discord.Bot):
        async def wait_for_message_or_edit(check, timeout=None):
            task_msg  = asyncio.create_task(bot.wait_for('message', check=check))
            task_edit = asyncio.create_task(bot.wait_for('message_edit',check=lambda before, after: check(after)))
            # wait for one to complete
            done, pending = await asyncio.wait(
                {task_msg, task_edit},
                return_when=asyncio.FIRST_COMPLETED,
                timeout=timeout
            )
            for t in pending:
                t.cancel()
            if not done:
                return None
            result = done.pop().result()
            # get 'after' for edits
            if isinstance(result, tuple):
                return result[1]
            return result
        return wait_for_message_or_edit
    
    class AppEmojis:
        def __init__(self, emojis:dict[str, discord.PartialEmoji]):
            self._emojis = emojis
            self._default = discord.PartialEmoji(
                name="unknown_emoji",
                id=1373376156010680350,
                animated=False
            )
        def __getitem__(self, key: str):
            return self._emojis.get(key, self._default)
        def get(self, key:str, default=None):
            return self._emojis.get(key, default)
        def keys(self):
            return self._emojis.keys()
        def values(self):
            return self._emojis.values()
        def items(self):
            return self._emojis.items()
        def __len__(self) -> int:
            return len(self._emojis)
        def __contains__(self, key: object) -> bool:
            return key in self._emojis
        def __iter__(self):
            return iter(self._emojis.items())
        def __repr__(self):
            return self._emojis.__repr__()

    def fetch_application_emojis_wrapper(self, bot:discord.Bot):
        async def fetch_application_emojis():
            url = f'https://discord.com/api/v10/applications/{bot.user.id}/emojis'
            headers = {'Authorization': f'Bot {bot.http.token}'}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        Log.warn(f"Failed to fetch application emojis for {bot.name}: {response.status} - {response.reason}")
                        return self.AppEmojis({})
                    data = await response.json()
                    if not isinstance(data, dict) or "items" not in data:
                        Log.warn(f"Failed to fetch application emojis for {bot.name}, response: {data}")
                        return self.AppEmojis({})
                    raw = data["items"]
            result = {}
            for emoji in raw:
                emoji_obj = discord.PartialEmoji(
                    name=emoji["name"],
                    id=int(emoji["id"]),
                    animated=emoji.get("animated", False)
                )
                result[emoji["name"]] = emoji_obj
            return self.AppEmojis(result)
        return fetch_application_emojis
