import discord
import asyncio
import random
from discord.ext import commands
from cogs import checks

class MuteRoulette():
    def __init__(self, bot):
        self.bot = bot

    # mute_roulette
    @commands.command(pass_context=True)
    async def mute_roulette(self, ctx):
        author_voice_channel = ctx.message.author.voice_channel
        voice_channel_members = author_voice_channel.voice_members
        random_member = random.choice(voice_channel_members)
        seconds = random.randint(1,10)

        if random.randrange(1,100) <= 10:
            seconds = 60

        if seconds == 60:
            await self.bot.say(':warning: Unlucky, {}! {} second mute.'.format(random_member.mention, seconds))
        else:
            await self.bot.say('Bad luck {}! {} second mute.'.format(random_member.mention, seconds))

        await self.bot.server_voice_state(random_member, mute=True)
        await asyncio.sleep(seconds)
        await self.bot.server_voice_state(random_member, mute=False) 

def setup(bot):
    bot.add_cog(MuteRoulette(bot))
