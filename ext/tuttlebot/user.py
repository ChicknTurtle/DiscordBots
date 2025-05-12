
import discord

from utils import Log

Log = Log()

def setup(bot):

    user_group = bot.create_group("user", "User related commands.")

    # mimic
    @user_group.command(name="mimic", description="Send a message as another user")
    async def user_mimic_command(ctx:discord.ApplicationContext, user:discord.Member, message:str):
        # blacklist
        if user.id in [
            716390085896962058 # poketwo
            ]:
            await ctx.respond(f"This user cannot be mimicked!", ephemeral=True)
            return
        await ctx.respond(f"Mimicking <@{user.id}>", ephemeral=True)
        try:
            webhook = await ctx.channel.create_webhook(name=user.name)
            if user.bot:
                name = user.name
            else:
                name = user.global_name
            await webhook.send(str(message), username=name, avatar_url=user.display_avatar, allowed_mentions=discord.AllowedMentions.none())
            await webhook.delete()
        except discord.errors.Forbidden:
            await ctx.respond(f"Bot does not have permission!", ephemeral=True)

    # user
    @user_group.command(name="info", description="Get info about a user")
    async def user_info_command(ctx:discord.ApplicationContext, user:discord.Member):

        general_lines = []
        server_lines = []

        # general info
        if user.bot:
            name = user.name
            username = user
        else:
            name = user.global_name
            username = user.name
        
        general_lines.append("\u200B")

        if user.bot:
            general_lines.append(":robot: **Bot**")

        if user.system:
            general_lines.append(":gear: **System**")
        
        if user.bot or user.system:
            general_lines.append("")

        general_lines.append(f"**Username:** `{username}`")
        general_lines.append("")
        general_lines.append(f"**Account Created:**")
        general_lines.append(f"<t:{round(user.created_at.timestamp())}:D>")
        
        # server info
        if type(user) == discord.Member:
            server_lines.append("> ")

            if user.guild_permissions.administrator:
                server_lines.append("> :shield: **Administrator**")
                server_lines.append("> ")

            roles = []
            for role in user.roles:
                roles.append(f"<@&{role.id}>")
            roles.remove(f"<@&{ctx.guild.id}>")

            if len(roles) > 0:
                roles = ' '.join(roles)
            else:
                roles = "`none`"

            server_lines.append(f"> **Roles:**")
            server_lines.append(f"> {roles}")
            server_lines.append("> ")
            server_lines.append(f"> **Joined {ctx.guild.name}:**")
            server_lines.append(f"> <t:{round(user.joined_at.timestamp())}:D>")

            server_lines.append("> \u200B")

        if ctx.guild is None:
            footer = "Use in a server for more information!"
        else:
            footer = None
        
        embedfields = [
            ('', '\n'.join(general_lines), True),
            ('', '\n'.join(server_lines), True)
        ]

        embed = bot.newembed(name, '', footer, thumbnail=user.avatar.url, fields=embedfields)
        await ctx.respond(embed=embed)
