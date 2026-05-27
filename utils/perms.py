
import discord

def get_missing_perms(channel, member, perms: discord.Permissions) -> discord.Permissions:
    has = channel.permissions_for(member)
    missing_value = perms.value & ~has.value
    return discord.Permissions(missing_value)
