
from time import time
from math import ceil
from datetime import datetime
from aiohttp import ClientSession
from io import BytesIO
import discord
from discord.ext import commands

from utils import Log, format_time

Log = Log()

def setup(bot):

    bot_group = bot.create_group("ai", "AI powered commands.")

    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": "Bearer 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"}

    async def query(payload):
        async with ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload) as response:
                return await response.read()

    # image
    @bot_group.command(name="image",description="Generate an image using ai")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ai_image_command(ctx:discord.ApplicationContext, prompt=discord.Option(str, max_length=1000, description="Image prompt")):
        original = await ctx.respond(f"**Generating Image...**\nPrompt: `{prompt}`")
        start_time = datetime.now() 
        image_bytes = await query({"inputs": prompt})
        end_time = datetime.now()
        total_time = end_time - start_time
        image_io = BytesIO(image_bytes)
        try:
            await original.edit_original_response(content=f"{prompt}\n**Generated in {format_time(total_time)}**", file=discord.File(fp=image_io, filename="generated_image.png"), allowed_mentions=discord.AllowedMentions.none())
        except discord.NotFound:
            image_io.seek(0)
            await ctx.send(f"-# {ctx.author.mention} used /ai image\n{prompt}\n**Generated in {format_time(total_time)}**", file=discord.File(fp=image_io, filename="generated_image.png"), allowed_mentions=discord.AllowedMentions.none())
    ai_image_command.helpdesc="[model used](<https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0>)"
    # image error
    @ai_image_command.error
    async def ai_image_command_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            cooldowntime = ceil(time()+error.retry_after)
            await ctx.respond(f"You're on cooldown! Try again <t:{cooldowntime}:R>.", ephemeral=True)
        else:
            raise error
