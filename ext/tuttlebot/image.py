
from time import time
from math import ceil
from datetime import datetime
import discord
from discord.ext import commands

from utils import Log, format_time, rgb_split_image, attachment_to_image, image_to_bufferimg

Log = Log()

def setup(bot):

    bot_group = bot.create_group("image", "Modify images with cool effects.")

    # rgbsplit
    @bot_group.command(name="rgbsplit",description="Split image pixels into red, green, and blue")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def image_rgbsplit_command(ctx:discord.ApplicationContext, attach=discord.Option(discord.Attachment, name='image', description="Image file to rgb split. Try a png or jpg file"), cmyk=discord.Option(bool, default=False, description="Display using cmyk instead of rgb"), horizontal=discord.Option(bool, default=False, description="Display colors horizontally instead of vertically")):
        start_time = datetime.now() 
        # make sure image is valid
        img = await attachment_to_image(attach)
        if not img:
            await ctx.respond(f"`{attach.filename}` isn't a valid image file! Try uploading a png or jpg file.\nYou uploaded: `{attach.content_type}`", ephemeral=True)
            return
        
        original = await ctx.respond(f"**RGB Splitting Image...**")
        # get image
        rgbimg = rgb_split_image(img, cmyk, horizontal)
        buffer = image_to_bufferimg(rgbimg)

        end_time = datetime.now()
        total_time = end_time - start_time
        file = discord.File(buffer, filename="rgb_split.png")
        try:
            await original.edit_original_response(content=f"RGB Split Image{" (CMYK)" if cmyk else ''}\n**Created in {format_time(total_time)}**", file=file, allowed_mentions=discord.AllowedMentions.none())
        except discord.NotFound:
            await ctx.send(f"-# {ctx.author.mention} used /image rgbsplit\nRGB Split Image\n**Created in {format_time(total_time)}**", file=file, allowed_mentions=discord.AllowedMentions.none())
    # rgbsplit error
    @image_rgbsplit_command.error
    async def image_rgbsplit_command_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            cooldowntime = ceil(time()+error.retry_after)
            await ctx.respond(f"You're on cooldown! Try again <t:{cooldowntime}:R>.", ephemeral=True)
        else:
            raise error
