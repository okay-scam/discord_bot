import discord
import asyncio
import bot
import operator
import time
import datetime
import pendulum
from cogs.utils import utils
from collections import OrderedDict
from tabulate import tabulate
from discord.ext import commands

class NewTimeCog():
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def newvoicetime(self, ctx):
        time_table = bot.db['new_time']
        highscores = dict()
        highscores_for_msg = OrderedDict()
        
        for user in time_table:
            highscores[user['user']] = user['time_in_seconds']
        
        highscores = sorted(highscores.items(),
                            key=operator.itemgetter(1),
                            reverse=True)

        for user in highscores[:10]:
            highscores_for_msg[user[0]] = utils.pretty_print_pendulum_duration(
                pendulum.duration(seconds=user[1]))

        highscores_msg = tabulate(
            highscores_for_msg.items(),
            tablefmt='plain',
            showindex=range(1,11)
        )
           
        await self.bot.say('```{}```'.format(highscores_msg))

    @commands.command(pass_context=True)
    async def newvoicetimeall(self, ctx):
        time_table = bot.db['new_time']
        highscores = dict()
        highscores_for_msg = OrderedDict()
        
        for user in time_table:
            highscores[user['user']] = user['time_in_seconds']
        
        highscores = sorted(highscores.items(),
                            key=operator.itemgetter(1),
                            reverse=True)

        for user in highscores:
            highscores_for_msg[user[0]] = utils.pretty_print_pendulum_duration(
                pendulum.duration(seconds=user[1]))

        highscores_msg = tabulate(
            highscores_for_msg.items(),
            tablefmt='plain',
            showindex=range(1,len(highscores)+1))
           
        await self.bot.say('```{}```'.format(highscores_msg))

def setup(bot):
    bot.add_cog(NewTimeCog(bot))