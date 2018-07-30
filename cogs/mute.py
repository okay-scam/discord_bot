import discord
import asyncio
from discord.ext import commands

class Mute():
    def __init__(self, bot):
        self.bot = bot

    # mute_channel
    @commands.command(pass_context=True)
    async def mute_channel(self, ctx, channel_name=""):
        if channel_name == "":
            # No channel name argument passed, use authors current voice channel
            channel = ctx.message.author.voice_channel
        else:
            channel = discord.utils.get(self.bot.get_all_channels(), name=channel_name)
        
        channel_members = channel.voice_members
        
        for member in channel_members:
            asyncio.ensure_future(self.bot.server_voice_state(member, mute=True))

    # unmute_channel
    @commands.command(pass_context=True)
    async def unmute_channel(self, ctx, channel_name=""):
        if channel_name == "":
            # No channel name argument passed, use authors current voice channel
            channel = ctx.message.author.voice_channel
        else:
            channel = discord.utils.get(self.bot.get_all_channels(), name=channel_name)
        
        channel_members = channel.voice_members
        
        for member in channel_members:
            asyncio.ensure_future(self.bot.server_voice_state(member, mute=False))

def setup(bot):
    bot.add_cog(Mute(bot))