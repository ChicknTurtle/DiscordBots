
import traceback
import discord

from bots import Bots
from data import Data
from utils import *

Log = Log()
Bots = Bots()
Data = Data()

async def handle_dev(bot:discord.Bot, msg:discord.Message):
    
    # Check owner            ChicknTurtle       Super Turtle
    if not msg.author.id in [957464464507166750,1026346464554782740]:
        return
    
    # build args
    args = msg.content.split(' ')
    args = [arg.strip() for arg in args]

    # console channel
    if msg.channel.id == 1312089859095138354:
        if bot.name == "TuttleBot":
            args.insert(0, bot.user.mention)
    
    # split second arg by newline (for codeblocks)
    if len(args) > 1:
        parts = args[1].split('\n', 1)
        args = args[:1] + parts + args[2:]
    
    # not enough args
    if len(args) == 1:
        return

    # starts with mention (or bot role mention)
    if args[0] != bot.user.mention:
        if args[0] != msg.guild.self_role.mention:
            return
    
    # error
    if args[1] == 'error':
        Log.log(f"{bot.name} | Throwing error...")
        await msg.add_reaction('👍')
        1+''
    
    # exec
    elif args[1] == 'exec':
        code = ' '.join(args[2:])
        code = code.lstrip("```py").strip('`')
        Log.log(f"{bot.name} | exec: {code}")
        response = await msg.reply("Executing...")
        try:
            result = None
            locals2 = locals()
            exec(code, globals(), locals2)
            result = locals2.get("result", None)
            if result != None:
                await response.edit(f"```py\n{result}\n```")
            else:
                await response.edit("Done.")
        except Exception as e:
            await response.edit(f"```py\n{traceback.format_exc()}\n```")
    
    # eval
    elif args[1] == 'eval':
        code = ' '.join(args[2:])
        code = code.strip("`")
        Log.log(f"{bot.name} | eval: {code}")
        response = await msg.reply("Evaluating...")
        try:
            output = str(eval(code))
            await response.edit(f"```py\n{output}\n```")
        except Exception as e:
            await response.edit(f"```py\n{traceback.format_exc()}\n```")
