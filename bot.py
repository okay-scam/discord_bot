import discord
import asyncio
import json
from discord.ext import commands
from cogs import checks

client = discord.Client()
bot = commands.Bot(command_prefix='!')

# Get Config
with open('config.json') as json_config:
    config = json.load(json_config)

# this specifies what extensions to load when the bot starts up
startup_extensions = [
    #"cogs.mute",
    "cogs.mute_roulette",
    "cogs.checks",
    "cogs.voice",
    "cogs.error_handler",
    #"cogs.exile",
]
allowed_channels = [
    "414701519733260288", #botspam
    "471262806533079041"  #bots
]


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

@bot.check
def is_allowed_channel(ctx):
    return checks.Checks.is_allowed_channel_check(ctx)

@bot.command()
async def load(extension_name):
    """Loads an extension."""
    try:
        bot.load_extension('cogs.{}'.format(extension_name))
    except (AttributeError, ImportError) as e:
        await bot.say("```py\n{}: {}\n```".format(type(e).__name__, str(e)))
        return
    await bot.say("{} loaded.".format(extension_name))

@bot.command()
async def unload(extension_name):
    """Unloads an extension."""
    bot.unload_extension('cogs.{}'.format(extension_name))
    await bot.say("{} unloaded.".format(extension_name))

@bot.command()
async def r():
    """ Reloads all extensions."""
    for extension in startup_extensions:
        try:
            bot.unload_extension(extension)
            print('Unloaded {}'.format(extension))
            bot.load_extension(extension)
            print('Loaded {}'.format(extension))
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load/unload extension {}\n{}'.format(extension, exc))

# Load Cogs
if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
            print('Loaded {}'.format(extension))
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))

    bot.run(config['token'])