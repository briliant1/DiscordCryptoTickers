import asyncio
import os
import random

import discord
import httpx
from discord.ext import commands
from discord_slash import SlashCommand
from dotenv import load_dotenv

load_dotenv()
client = commands.Bot(command_prefix=";")
slash = SlashCommand(client, sync_commands=True)

main_currency_api = os.environ['MAIN_CURRENCY_NAME']
main_currency_symbol = os.environ['MAIN_CURRENCY_SYMBOL']
currency_to_show = os.environ['CURRENCY_TO_SHOW']
currencies_to_watch = os.environ['VS_CURRENCIES']
wait_duration = int(os.environ['WAIT_DURATION'])
discord_token = os.environ['DISCORD_TOKEN']

coingecko = f"https://api.coingecko.com/api/v3/simple/price?ids={main_currency_api}&vs_currencies={currencies_to_watch}"


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    asyncio.create_task(task_update_activity())


def get_coingecko_data():
    with httpx.Client(timeout=None) as httpx_client:
        response = httpx_client.get(coingecko)
        data = response.json()
        return data


def value_of_currency_to_show():
    return float(get_coingecko_data()[main_currency_api][currency_to_show])


def watch_secondary_currencies():
    split_second_currency = [x for x in currencies_to_watch.split(",") if x != currency_to_show]
    currencies = []
    for second_currency in split_second_currency:
        data = {
            "symbol": second_currency,
            "value": float(get_coingecko_data()[main_currency_api][second_currency])
        }
        currencies.append(data)
    return currencies


async def task_update_activity():
    await client.wait_until_ready()
    while not client.is_closed():
        for guild in client.guilds:
            await guild.me.edit(nick=f"{value_of_currency_to_show():,} {currency_to_show.upper()}/{main_currency_symbol}")

        status = []
        for data in watch_secondary_currencies():
            status_name = f"{data['value']:,} {data['symbol'].upper()}"
            status.append(status_name)

        activity_status = random.choice(status)

        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=activity_status))
        await asyncio.sleep(wait_duration)


client.run(discord_token)