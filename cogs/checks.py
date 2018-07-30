from discord.ext import commands
from pprint import pprint

allowed_channels = [
    "414701519733260288", #botspam
    "471262806533079041"  #bots
]

class Checks():
    def __init__(self, bot):
        self.bot = bot
        self.allowed_channels = allowed_channels

    def is_allowed_channel_check(ctx):
        channel = ctx.message.channel.id
        return channel in allowed_channels

def setup(bot):
    bot.add_cog(Checks(bot))