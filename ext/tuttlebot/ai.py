
import datetime
import aiohttp
import io
import discord

from utils import *

Log = Log()

def setup(bot):

    bot_group = bot.create_group("ai", "AI powered commands.")

    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": "Bearer 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"}

    async def query(payload):
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload) as response:
                return await response.read()

    # image
    @bot_group.command(name="image",description="Generate an image using ai",)
    async def ai_image_command(ctx:discord.ApplicationContext, prompt:str):
        original = await ctx.respond(f"**Generating Image...**\nPrompt: `{prompt}`")

        start_time = datetime.now() 
        image_bytes = await query({"inputs": prompt})
        end_time = datetime.now()
        total_time = end_time - start_time

        image_io = io.BytesIO(image_bytes)

        try:
            await original.edit_original_response(content=f"{prompt}\n**Generated in {format_time(total_time)}**", file=discord.File(fp=image_io, filename="generated_image.png"))
        except Exception as e:
            await original.edit_original_response(content=f"**Generating Image...**\nThere was an error! The API may have broken.")
            raise(e)
    # add help description
    ai_image_command.helpdesc="[model used](<https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0>)"
