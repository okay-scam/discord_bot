import discord
import datetime
import asyncio


class NewTimeCog():
    def __init__(self, bot):
        self.bot = bot

    async def store_time_task(self):
        await client.wait_until_ready()
        time_table = bot.db['time']
        sessions_table = bot.db['sessions']

        while not bot.client.is_closed():
            members = []
            try:
                channels = bot.server.channels
                for channel in channels:
                    if channel.type == 'voice':
                        members += channel.voice_members
                for member in members:
                    print('something like {}.total_time += 60s'.format(member))
                await asyncio.sleep(60)
            except Exception as e:
                print(str(e))
                await asyncio.sleep(60)