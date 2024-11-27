
import discord

from utils import *

Log = Log()

class HelpSelect(discord.ui.Select):
    def __init__(self, bot:discord.Bot):
        options = []
        for command in bot.commands:
            if command.name != 'help':
                options.append(discord.SelectOption(label=f"{command.name} - {command.description}", value=command.name))

        super().__init__(
            placeholder = "Select a command",
            min_values = 1, max_values = 1,
            options = options,
        )
    async def callback(self, interaction:discord.Interaction):
        bot:discord.Bot = interaction.client
        group:discord.SlashCommandGroup = bot.get_command(self.values[0])
        try:
            commands:list[discord.SlashCommand] = [subcommand for subcommand in group.walk_commands()]
        except AttributeError:
            commands:list[discord.SlashCommand] = [group]
        helpdesc = f" {group.helpdesc}" if hasattr(group, 'helpdesc') else ""
        embed:discord.Embed = bot.newembed(title=f"Help for /{group.name}", description=f"{group.description}{helpdesc}")
        for command in commands:
            syntax = command.name
            for option in command.options:
                if option.required:
                    syntax = f"{syntax} <{option.name}>"
                else:
                    default = f"={getattr(option, 'default', '')}"
                    syntax = f"{syntax} [{option.name}{default}]"
            helpdesc = f"\n{command.helpdesc}" if hasattr(command, 'helpdesc') else ""
            description = f"{command.description}{helpdesc}\nSyntax: `{syntax}`"
            embed.add_field(name=command.name, value=description, inline=True)
        await interaction.response.send_message(None, embed=embed, ephemeral=True)

class HelpView(discord.ui.View):
    def __init__(self, bot:discord.Bot):
        self.bot = bot
        super().__init__(timeout=None)
        self.add_item(HelpSelect(self.bot))

def setup(bot:discord.Bot):

    @bot.command(name="help", description="Get help for the bot")
    async def help_command(ctx:discord.ApplicationContext):
        view = HelpView(bot)
        embed = bot.newembed("Help Menu", "Choose a category to get help for below:")
        await ctx.respond(embed=embed, view=view)
