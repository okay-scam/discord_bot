import discord
import asyncio
import math
from pprint import pprint
from collections import Counter
from discord.ext import commands

class Votes():
    def __init__(self, bot):
        self.bot = bot
        self.vote = None
        self.vote_in_progress = None
        self.vote_threshold_percentage = 50 # % of users in voice channel for vote to pass
        self.vote_threshold = 0 # Votes required to pass this vote
        self.accepted_emojis = ['✅', '❌']
        self.voice_members_count = None
        self.embed = None
        self.voter_ids = []
        self.voted_user = None

    async def end_vote(self, result):
        self.vote_in_progress = False

        if result == 'pass':
            await self.bot.delete_message(self.vote)
            self.embed = discord.Embed(colour=discord.Colour(1376000))
            self.embed.description = '✅ Vote passed!'
            await self.mute_user(self.voted_user)
        elif result == 'fail':
            await self.bot.delete_message(self.vote)
            self.embed = discord.Embed(colour=discord.Colour(0xff0000))
            self.embed.description = '❌ Vote failed.'
        elif result == 'timeout':
            await self.bot.delete_message(self.vote)
            self.embed = discord.Embed(colour=discord.Colour(0xff0000))
            self.embed.description = '❌ Not enough votes, vote failed.'
        else:
            await self.bot.send_message(self.vote.channel, "```Something went wrong... maybe try again?```")
            return
        await self.bot.send_message(self.vote.channel, embed=self.embed)
    
    async def update_voter_ids(self):
        msg = await self.bot.get_message(self.vote.channel, self.vote.id)
        
        users = []
        for react in msg.reactions:
            users += await self.bot.get_reaction_users(react)
     
        self.voter_ids = list(o.id for o in users)

    async def mute_user(self, user):
        await self.bot.server_voice_state(user, mute=True)


    @commands.command(pass_context=True)
    async def vm(self, ctx, user: discord.User=None):
        # Get voice channel statistics and vote thresholds at time vote is called
        self.voice_members_count = len(ctx.message.author.voice_channel.voice_members)
        self.vote_threshold = math.ceil((self.voice_members_count * (self.vote_threshold_percentage/100))+1) # +1 to account for bots initial "votes"

        # Get user to mute
        self.voted_user = user

        # Check if that user is in your channel
        voice_channel_members = ctx.message.author.voice_channel.voice_members
        if user not in voice_channel_members:
            await self.bot.say('```That user is not in your voice channel```')
            return

        # Then we check if there are enough people in the channel to start a vote (min = 2)
        if self.voice_members_count <= 2:
            await self.bot.say('```Minimum of 2 users are required in a channel to start a vote.```')
            return

        # First, we check is vote is already in progress
        if self.vote_in_progress:
            await self.bot.say('Vote in progress, please wait...')
            return
        
        # Build embed
        self.embed = discord.Embed(colour=discord.Colour(0xff0000))
        self.embed.description = '{} wants to mute {}\n\n{}'.format(ctx.message.author.mention, self.voted_user.mention, '**Vote now!**')
        self.embed.set_footer(text='{} or more ✅ to pass!'.format(self.vote_threshold))
        self.embed.add_field(name=':white_check_mark:', value='Yes', inline=True)
        self.embed.add_field(name=':x:', value='No', inline=True)

        # Send vote embed & set vote state
        self.vote = await self.bot.say(embed=self.embed)
        self.vote_in_progress = True

        # Add reacts to vote message
        await self.bot.add_reaction(self.vote, '✅')
        await self.bot.add_reaction(self.vote, '❌')

        # Update current voter ids
        await self.update_voter_ids()

        # Vote timeout
        await asyncio.sleep(30)
        # Check that the vote hasn't ended (likely from passing the threshold)
        if self.vote_in_progress:
            # Set vote state
            await self.end_vote('timeout')


    # On react adds  
    async def on_reaction_add(self, reaction, user):
        # Ignore to bot reacts
        if user.id == self.bot.user.id:
            print('BOT REACT. IGNORE IGNORE!')
            return
            
        # Only track react adds to our vote message
        if reaction.message.id != self.vote.id:
            return

        if user.id in self.voter_ids:
            print('Already voted')
            await self.bot.remove_reaction(reaction.message, reaction.emoji, user)
        else:
            await self.update_voter_ids()

        # Remove non-accepted/non-vote emojis
        if reaction.emoji not in self.accepted_emojis:
            await self.bot.remove_reaction(reaction.message, reaction.emoji, user)
        
        # Yes react
        if reaction.emoji == '✅':
            if reaction.count >= self.vote_threshold:
                await self.end_vote('pass')
                   
        # No react
        if reaction.emoji == '❌':
            if reaction.count >= self.vote_threshold:
                await self.end_vote('fail')

    # On react removes
    async def on_reaction_remove(self, reaction, user):
        # Ignore to bot reacts
        if user.id == self.bot.user.id:
            print('BOT REACT. IGNORE IGNORE!')
            return
            
        # Only track react adds to our vote message
        if reaction.message.id != self.vote.id:
            return

        await self.update_voter_ids()
        await asyncio.sleep(1)

def setup(bot):
    bot.add_cog(Votes(bot))