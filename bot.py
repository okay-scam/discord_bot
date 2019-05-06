import discord
import asyncio
import json
import dataset
import requests
from cogs import checks, voice
from discord.ext import commands

client = discord.Client()
bot = commands.Bot(command_prefix='!')

# Get Config
with open('/home/ubuntu/discord_bot/config.json') as json_config:
    config = json.load(json_config)

# Initialise database connection
db = dataset.connect('sqlite:////home/ubuntu/discord_bot/sqlite3/discord.db')

# this specifies what extensions to load when the bot starts up
startup_extensions = [
    "cogs.checks",
    "cogs.voice",
    "cogs.votes",
    "cogs.time",
    "cogs.mort_checker",
    "cogs.uploads",
]
allowed_channels = [
    "414701519733260288", #botspam
    "471262806533079041"  #bot
]


def get_user_roles():
    users = bot.get_server('299756881004462081').members
    user_roles_list = {}
    for user in users:
        user_roles_list[user.name] = [role.name for role in user.roles
            if role.name != '']

    return user_roles_list


def update_user_roles(user_roles):
    db['user_roles'].drop()
    for user, roles in user_roles.items():
        db['user_roles'].upsert(
            dict(user=user, roles=','.join(roles)), ['user'])

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    update_user_roles(get_user_roles())
    db['sound_queue'].drop()

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


# Calls bot to join user channel
async def summon(user):
    return await bot.join_voice_channel(get_user_channel(user))

async def play_queued_sound(user, sound):
    ec2_url = 'https://s3-ap-southeast-2.amazonaws.com/scamdiscordbot/'
    mp3_url = '{}{}.mp3'.format(ec2_url, sound)
    r = requests.head(mp3_url)

    # Summon to channel
    voice = await summon(user)

    if not voice:
        return
    try:
        player = await voice.create_ytdl_player(mp3_url)
        player.start()
        while player.is_playing():
            pass
        await voice.disconnect()
    except discord.ClientException as e:
        print(e)
        await voice.disconnect()

def add_to_queue(sound, user):
    db['sound_queue'].insert(dict(user=user, sound=sound, state='ready'))
    return 'Added {sound} by {user} to queue'.format(sound=sound, user=user)

def remove_sound_from_queue(id):
    return db['sound_queue'].delete(id=id)

async def poll_sound_queue_loop():
    await bot.wait_until_ready()
    loop_iter = 1 # (seconds) Loop will run and increment stats on this value

    while not bot.is_closed:
        await asyncio.sleep(loop_iter)

        try:
            sound = list(db['sound_queue'])[0]['sound']
        except IndexError:
            sound = None

        if sound != None:
            user = list(db['sound_queue'])[0]['user']
            id = list(db['sound_queue'])[0]['id']
            await play_queued_sound(user, sound)
            remove_sound_from_queue(id)

def get_user_channel(user):
    user = discord.utils.get(
        bot.get_server('299756881004462081').members,
        name=user)
    return user.voice.voice_channel

async def server_roles_loop():
    await bot.wait_until_ready()
    loop_iter = 300 # (seconds) Loop will run and increment stats on this value

    while not bot.is_closed:
        await asyncio.sleep(loop_iter)
        update_user_roles(get_user_roles())

async def voice_time_loop():
    await bot.wait_until_ready()
    loop_iter = 60 # (seconds) Loop will run and increment stats on this value

    while not bot.is_closed:
        await asyncio.sleep(loop_iter)

        server = bot.get_server('299756881004462081')
        voice_channels = (channel for channel in server.channels 
                            if channel.type is discord.ChannelType.voice)

        voice_members_generator = [
            channel.voice_members for channel in voice_channels
            if len(channel.voice_members) > 0
            and channel != server.afk_channel
        ]

        current_voice_members = [
            '{}#{}'.format(voice_member.name, voice_member.discriminator) 
            for sublist in voice_members_generator 
            for voice_member in sublist]

        previous_voice_members = [user['user'] for user in db['voice_users']]

        # if you were in the channel before, and you're in here now
        #  += seconds to your time
        new_time_table = db['new_time']

        users_to_increment = [member for member in current_voice_members
                                if member in previous_voice_members]

        for user in users_to_increment:
            db_user = new_time_table.find_one(user=user)
            incremented_time = db_user['time_in_seconds'] + loop_iter 
            new_time_table.upsert(dict(user=user, time_in_seconds=incremented_time), ['user'])

        # Clear voice_users table fresh for next check
        db['voice_users'].delete()
        for member in current_voice_members:
            db['voice_users'].upsert(dict(user=member), ['user'])


# Load Cogs
if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
            print('Loaded {}'.format(extension))
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))
    
    bot.loop.create_task(voice_time_loop())
    bot.loop.create_task(server_roles_loop())
    bot.loop.create_task(poll_sound_queue_loop())
    bot.run(config['token'])
