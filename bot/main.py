import asyncio
import os
from itertools import cycle

import aiohttp
import discord
import random
from discord.ext import commands, tasks
from discord_slash import SlashCommand
from dotenv import load_dotenv

load_dotenv()
client = commands.Bot(command_prefix=";")
slash = SlashCommand(client, sync_commands=True)

main_currency_api = os.environ['MAIN_CURRENCY_NAME']
main_currency_symbol = os.environ['MAIN_CURRENCY_SYMBOL']
currency_to_show = os.environ['CURRENCY_TO_SHOW']
currencies_to_watch = os.environ['VS_CURRENCIES']
discord_token = os.environ['DISCORD_TOKEN']

coingecko = f"https://api.coingecko.com/api/v3/simple/price?ids={main_currency_api}&vs_currencies={currencies_to_watch}"


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    task_update_activity.start()


async def get_coingecko_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(coingecko) as resp:
            data = await resp.json()
            return data


async def value_of_currency_to_show():
    return float((await get_coingecko_data())[main_currency_api][currency_to_show])


async def watch_secondary_currencies():
    split_second_currency = [x for x in currencies_to_watch.split(",") if x != currency_to_show]
    currencies = []
    for second_currency in split_second_currency:
        data = {
            "symbol": second_currency,
            "value": float((await get_coingecko_data())[main_currency_api][second_currency])
        }
        currencies.append(data)
    return currencies


@tasks.loop(seconds=5.0)
async def task_update_activity():
    for guild in client.guilds:
        await guild.me.edit(nick=f"{(await value_of_currency_to_show()):,} {currency_to_show.upper()}/{main_currency_symbol}")

    status = []
    secondary_currency = await watch_secondary_currencies()
    for data in secondary_currency:
        status_name = f"{data['value']:,} {data['symbol'].upper()}"
        status.append(status_name)
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=random.choice(status)))


client.run(discord_token)
