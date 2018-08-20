import discord
import asyncio
import datetime
import operator
from tabulate import tabulate
import bot
from pprint import pprint
from collections import defaultdict
from discord.ext import commands

class TimeCog():
    def __init__(self, bot):
        self.bot = bot

    async def on_voice_state_update(self, before, after):
        time_table = bot.db['time']
        sessions_table = bot.db['sessions']
        user = '{}#{}'.format(after.name, after.discriminator)

        if after.id == '471255864238538753':
            return
       
        # User joins voice channel
        if (before.voice_channel is None
            and after.voice_channel is not None
            or before.voice_channel is before.server.afk_channel):

            user_session_row = sessions_table.find_one(user_id=after.id)
            join_timestamp = datetime.datetime.now()
     
            if user_session_row is None:
                print('User does not have any prior sessions, creating entry')
                sessions_table.insert(dict(user_id=after.id, name=user, session=None))
                user_session_row = sessions_table.find_one(user_id=after.id)

            # Find and delete any sessions that went wrong (ie. bot crashed, user left and never got a leave timestamp)
            for row in list(time_table.find(user_id=after.id)):
                if row['join_timestamp'] is None and row['leave_timestamp'] is not None:
                    time_table.delete(id=row['id'])

            time_table.insert(dict(user_id=after.id, user=user, join_timestamp=join_timestamp, leave_timestamp=join_timestamp))
            sessions_table.update(dict(user_id=after.id, session='active'), ['user_id'])
            print('{} join_timestamp set to {}'.format(after.name, join_timestamp))


        # User leaves voice
        if (before.voice_channel is not None
            and after.voice_channel is None
            or after.voice_channel is after.server.afk_channel):

            sessions_table.update(dict(user_id=after.id, session='inactive'), ['user_id'])
            for row in list(time_table.find(user_id=after.id)):
                if row['join_timestamp'] == row['leave_timestamp']:
                    leave_timestamp = datetime.datetime.now()
                    time_table.update(dict(id=row['id'], leave_timestamp=leave_timestamp), ['id'])
                    delta = time_table.find_one(id=row['id'])
                    session_time = delta['leave_timestamp'] - delta['join_timestamp']
                    await self.bot.send_message(self.bot.get_channel('471262806533079041'), 
                        '{} session time: {} minute(s), {} second(s)'.format(after.name, round(session_time.seconds/60), session_time.seconds % 60))

    @commands.command(pass_context=True, no_pm=True)
    async def voicetime(self, ctx):
        time_table = bot.db['time']
        highscores = defaultdict(list)

        for entry in time_table:
            highscores[entry['user']].append(entry['leave_timestamp'] - entry['join_timestamp'])
            
        for user in highscores:
            highscores[user] = sum(highscores[user], datetime.timedelta())
 
        highscores = sorted(highscores.items(), key=operator.itemgetter(1), reverse=True)
        await self.bot.say('```{}```'.format(
            tabulate(highscores[:10], tablefmt='plain', showindex=range(1,11))))



def setup(bot):
    bot.add_cog(TimeCog(bot))
