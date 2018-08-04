from discord.ext import commands
import bot


class Checks:
    def __init__(self, bot):
        self.bot = bot

    def is_allowed_channel_check(ctx):
        channel = ctx.message.channel.id
        return channel in bot.allowed_channels


def setup(bot):
    bot.add_cog(Checks(bot))