import discord
import asyncio
#from cogs.checks import allowed_channels
import bot
from discord.ext import commands

class ErrorHandler():
    def __init__(self, bot):
        self.bot = bot

    async def on_command_error(self, error, ctx):
        # (Global, likely) Check Faliure
        if isinstance(error, discord.ext.commands.errors.CheckFailure):      
            # Build allowed_channels_objs list
            allowed_channels_mention_objs = []
            allowed_channels_objs = []
            for channel in bot.allowed_channels:
                allowed_channels_mention_objs.append(self.bot.get_channel(channel).mention)
                allowed_channels_objs.append(self.bot.get_channel(channel))

            await self.bot.delete_message(ctx.message)
            await asyncio.sleep(0.1)
            for channel in allowed_channels_objs:
                await self.bot.send_message(channel, 'Sorry {}, commands only work in these channels: {}'.format(ctx.message.author.mention, ' '.join(allowed_channels_mention_objs)))
        else:
            print(error)

def setup(bot):
    bot.add_cog(ErrorHandler(bot))
