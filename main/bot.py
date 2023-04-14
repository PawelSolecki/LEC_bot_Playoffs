from async_timeout import asyncio
import discord
from discord.ext import commands
from datetime import date, datetime
import os
import sys

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import resources.const as const
import controllers.leaguepedia as leaguepedia
import resources.secret_file as secret

#leaguepedia.constructMatches()
intents = discord.Intents.default()
intents = discord.Intents.all()

intents.typing = False
intents.presences = False
intents.members = True

client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix=">",intents=intents,help_command=None)
TOKEN = secret.bot_token

path_to_cog="main/cogs"
async def load_all_cogs():
    for filename in os.listdir(path_to_cog):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    await load_all_cogs()
    await bot.start(TOKEN)
asyncio.run(main())