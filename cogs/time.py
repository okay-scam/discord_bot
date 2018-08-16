import discord
import asyncio
import pandas
import bot
from pprint import pprint
from discord.ext import commands

class TimeCog():
    def __init__(self, bot):
        self.bot = bot

    async def on_voice_state_update(self, before, after):
        table = bot.db['time']
        user = '{}#{}'.format(after.name, after.discriminator)

        if (after.id is not '471255864238538753'
            and after.voice_channel is not after.server.afk_channel):

            # User leaves voice channel
            if (before.voice_channel is not None
                and after.voice_channel is None):
                table.upsert(dict(user_id=after.id, user=user, join_timestamp=pandas.Timestamp.now()), ['join_timestamp'])

            # User joins voice channel
            if (before.voice_channel is None
                and after.voice_channel is not None):
                table.upsert(dict(user_id=after.id, user=user, leave_timestamp=pandas.Timestamp.now()), ['user_id'])
                pprint(list(table))


def setup(bot):
    bot.add_cog(TimeCog(bot))