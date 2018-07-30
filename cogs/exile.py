import discord
import asyncio
import random
from discord.ext import commands

class ExileGame():
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def exile(self, ctx, user: discord.User=None):
        # Get list of members in authors voice channel
        voice_channel_members = ctx.message.author.voice_channel.voice_members
        # Remove author from list, unless author is the only person in the list.
        if not all(p == ctx.message.author for p in voice_channel_members):
           if ctx.message.author in voice_channel_members: # This is a hack to stop an exception
                voice_channel_members.remove(ctx.message.author)

        # Mute time
        seconds = random.randint(5,30)

        # Roll 1/3 chance to exile yourself
        if random.randrange(1,100) >= 33:
            if user == None:
                exiled_member = random.choice(voice_channel_members)
            else:
                exiled_member = user
            await self.bot.say('{} has been exiled for {} seconds'.format(exiled_member.mention, seconds))
        else:
            await self.bot.say('Unlucky. You have exiled yourself for {} seconds! :skull:'.format(seconds))
            exiled_member = ctx.message.author

        exiled_members_roles = exiled_member.roles
        
        exiled_members_channel = exiled_member.voice_channel
        exiled_role = discord.utils.get(ctx.message.server.roles, id='472715824247865345')
        afk_channel = ctx.message.server.afk_channel

        # Exile
        await self.bot.remove_roles(exiled_member, *exiled_members_roles)
        await self.bot.add_roles(exiled_member, exiled_role) # Exiled role
        await self.bot.move_member(exiled_member, afk_channel)

        # Cooldown time
        await asyncio.sleep(seconds)

        # Reinstate
        await self.bot.add_roles(exiled_member, *exiled_members_roles)
        await self.bot.remove_roles(exiled_member, exiled_role) # Exiled role
        await self.bot.move_member(exiled_member, exiled_members_channel)

def setup(bot):
    bot.add_cog(ExileGame(bot))