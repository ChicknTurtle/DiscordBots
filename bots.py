
import discord
from dotenv import load_dotenv
import os

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

        self.tuttlebot = discord.AutoShardedBot(intents=intents, help_command=None)
        self.tuttlebot.name = "TuttleBot"
        self.tuttlebot.token = os.getenv('tuttlebot')
        self.tuttlebot.color = 0x309c58
        if self.tuttlebot.token:
            self._bots.append(self.tuttlebot)

        self.neoturtle = discord.AutoShardedBot(intents=intents, help_command=None)
        self.neoturtle.name = "NeoTurtle"
        self.neoturtle.token = os.getenv('neoturtle')
        self.neoturtle.color = 0x00ff00
        self.neoturtle.customemojis = {
            'neotoken':'<:neotoken:1289435632720154655>',
            'neotoken2':'<:neotoken2:1309191147733651536>'
            }
        if self.neoturtle.token:
            self._bots.append(self.neoturtle)
        
        self.splatdrone = discord.AutoShardedBot(intents=intents, help_command=None)
        self.splatdrone.name = "Splatdrone"
        self.splatdrone.token = os.getenv('splatdrone')
        self.splatdrone.color = 0x76f5f3
        if self.splatdrone.token:
            self._bots.append(self.splatdrone)

        for bot in self:
            bot.newembed = self.newembed_wrapper(bot)
        
    def newembed_wrapper(self, bot):
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
    
    def __iter__(self):
        return iter(self._bots)
    
    def __getitem__(self, index):
        return self._bots[index]
