import discord
import asyncio
from discord.ext import commands

class TemplateCog():
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def hello(self, ctx):
        await self.bot.say('Hello {}'.format(ctx.message.author.mention))

def setup(bot):
    bot.add_cog(TemplateCog(bot))