
from time import time
from math import ceil
from datetime import datetime
from aiohttp import ClientSession
from io import BytesIO
import discord
from discord.ext import commands

from utils import Log, format_time, rgb_split_image, attachment_to_image, image_to_bufferimg

Log = Log()

def setup(bot):

    bot_group = bot.create_group("image", "Modify images with cool effects.")

    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": "Bearer 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"}

    async def query(payload):
        async with ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload) as response:
                return await response.read()

    # ai
    @bot_group.command(name="ai",description="Generate an image using ai")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def image_ai_command(ctx:discord.ApplicationContext, prompt=discord.Option(str, max_length=1000, description="Image prompt")):
        original = await ctx.respond(f"**Generating Image...**\nPrompt: `{prompt}`")
        start_time = datetime.now() 
        image_bytes = await query({"inputs": prompt})
        end_time = datetime.now()
        total_time = end_time - start_time
        image_io = BytesIO(image_bytes)
        file = discord.File(image_io, filename="generated_image.png")
        try:
            await original.edit_original_response(content=f"{prompt}\n**Generated in {format_time(total_time)}**", file=file, allowed_mentions=discord.AllowedMentions.none())
        except discord.NotFound:
            image_io.seek(0)
            await ctx.send(f"-# {ctx.author.mention} used /ai image\n{prompt}\n**Generated in {format_time(total_time)}**", file=file, allowed_mentions=discord.AllowedMentions.none())
    image_ai_command.helpdesc="[model used](<https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0>)"
    # ai error
    @image_ai_command.error
    async def image_ai_command_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            cooldowntime = ceil(time()+error.retry_after)
            await ctx.respond(f"You're on cooldown! Try again <t:{cooldowntime}:R>.", ephemeral=True)
        else:
            raise error

    # rgbsplit
    @bot_group.command(name="rgbsplit",description="Split image pixels into red, green, and blue")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def image_rgbsplit_command(ctx:discord.ApplicationContext, attach=discord.Option(discord.Attachment, name='image', description="Image file to rgb split. Try a png or jpg file")):
        # make sure image is valid
        img = await attachment_to_image(attach)
        if not img:
            await ctx.respond(f"`{attach.filename}` isn't a valid image file! Try uploading a png or jpg file.\nYou uploaded: `{attach.content_type}`", ephemeral=True)
            return
        
        original = await ctx.respond(f"**RGB Splitting Image...**")
        start_time = datetime.now() 
        # get image
        rgbimg = rgb_split_image(img)
        buffer = image_to_bufferimg(rgbimg)

        end_time = datetime.now()
        total_time = end_time - start_time
        file = discord.File(buffer, filename="rgb_split.png")
        try:
            await original.edit_original_response(content=f"RGB Split Image\n**Created in {format_time(total_time)}**", file=file, allowed_mentions=discord.AllowedMentions.none())
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
