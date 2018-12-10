import discord
import asyncio
import math
import bot
import dataset
import pdb
from pprint import pprint
from collections import Counter
from discord.ext import commands

class MortChecker():
    def __init__(self, bot):
        self.bot = bot
        self.vote = None
        self.vote_in_progress = None
        self.vote_threshold_percentage = 1 # % of users in voice channel for vote to pass
        self.vote_threshold = 0 # Votes required to pass this vote
        self.accepted_emojis = ['✅', '❌']
        self.voice_members_count = None
        self.embed = None
        self.voter_ids = []
        self.mentioned_user = None
        self.vote_type = None
        self.server = None

    async def vote_end(self, result):
        self.vote_in_progress = False
        await self.vote_action(result)

    async def update_voter_ids(self):
        msg = await self.bot.get_message(self.vote.channel, self.vote.id)
        
        users = []
        for react in msg.reactions:
            users += await self.bot.get_reaction_users(react)
     
        self.voter_ids = list(o.id for o in users)
  
    async def vote_start(self, ctx, vote_type):
        # Initialise initial vote statistics and vote thresholds
        self.vote_type = vote_type
        if vote_type is not 'mort_checker':
            self.voice_members_count = len(ctx.message.author.voice_channel.voice_members)
            self.vote_threshold = math.ceil((self.voice_members_count * (self.vote_threshold_percentage/100))+1) # +1 to account for bots initial "votes"
            self.server = ctx.message.server
        else:
            self.voice_members_count = len(ctx.voice_channel.voice_members)
            self.vote_threshold = math.ceil((self.voice_members_count * (self.vote_threshold_percentage/100))+1) # +1 to account for bots initial "votes"
            self.server = ctx.server         

        # Check if that user is in your channel
        # CAN WE REPLACE THIS WITH A @CHECK?
        if vote_type is not 'mort_checker':
            voice_channel_members = ctx.message.author.voice_channel.voice_members
            if self.mentioned_user not in voice_channel_members:
                await self.bot.say('```User must be in your voice channel to start a vote```')
                return
        
        # Then, we check is vote is already in progress
        # CAN WE REPLACE THIS WITH A @CHECK?
        if self.vote_in_progress:
            await self.bot.say('Vote in progress, please wait...')
            return
        
        # Build vote message embed object
        if self.vote_type == 'mort_checker':
            vote_type_string = 'Did Mort Brealey leave without saying bye?'
        else:
            self.bot.say('```Error: Unknown vote type```')
            return
            
        self.embed = discord.Embed(colour=discord.Colour(0xff0000))
        self.embed.description = '{}\n\n{}'.format(vote_type_string, '**Vote now!**')
        self.embed.set_footer(text='{} or more ✅ to pass!'.format(self.vote_threshold))
        self.embed.add_field(name=':white_check_mark:', value='Yes', inline=True)
        self.embed.add_field(name=':x:', value='No', inline=True)

        # Send vote embed & set vote state
        self.vote_in_progress = True
        text_channel = ctx.server.get_channel('299756881004462081')
        self.vote = await self.bot.send_message(text_channel, embed=self.embed)
        #self.vote = await self.bot.say(embed=self.embed)
        # Add reacts to vote message
        await self.bot.add_reaction(self.vote, '✅')
        await self.bot.add_reaction(self.vote, '❌')

        # Update current voter ids list
        await self.update_voter_ids()        

        # Vote timeout
        await asyncio.sleep(180)
        # Check that the vote hasn't ended (likely from passing the threshold)
        if self.vote_in_progress:
            # Set vote state
            await self.vote_end('timeout')

    async def vote_action(self, result):
        if result == 'fail':
            await self.bot.delete_message(self.vote)
            self.embed = discord.Embed(colour=discord.Colour(0xff0000))
            self.embed.description = '❌ Vote failed.'
        elif result == 'pass':
            await self.bot.delete_message(self.vote)
            self.embed = discord.Embed(colour=discord.Colour(1376000))
            self.embed.description = '✅ Vote passed!'
        elif result == 'timeout':
            await self.bot.delete_message(self.vote)
            self.embed = discord.Embed(colour=discord.Colour(0xff0000))
            self.embed.description = '❌ Not enough votes, vote failed.'
        elif result == 'force_end':
            await self.bot.delete_message(self.vote)
            self.embed = discord.Embed(colour=discord.Colour(0xff0000))
            self.embed.description = 'Vote cancelled.'
        else:
            await self.bot.send_message(self.vote.channel, "```Something went wrong... maybe try again?```")
            return
        await self.bot.send_message(self.vote.channel, embed=self.embed)

        if result == 'pass':
            if self.vote_type == 'mort_checker':
                mort_table =  bot.db['mort_checker']
                mort_shame_count = mort_table.find_one(name='mort')['mort_checker_count'] + 1
                mort_table.upsert(dict(name='mort', mort_checker_count=mort_shame_count), ['name'])
                mort_user = self.bot.get_server('299756881004462081').get_member('342511480685461514')
                mort_new_user = mort_user.nick.split('(')[0].strip()
                await self.bot.change_nickname(mort_user, '{} ({})'.format(mort_new_user, mort_shame_count))
        return

    # On react adds  
    async def on_reaction_add(self, reaction, user):
        # Ignore to bot reacts
        if user.id == self.bot.user.id or user.id == '342511480685461514':
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
                await self.vote_end('pass')

        # No react
        if reaction.emoji == '❌':
            if reaction.count >= self.vote_threshold:
                await self.vote_end('fail')

    # On react removes
    async def on_reaction_remove(self, reaction, user):
        # Ignore to bot reacts
        if user.id == self.bot.user.id:
            return
            
        # Only track react adds to our vote message
        if reaction.message.id != self.vote.id:
            return

        await self.update_voter_ids()
        await asyncio.sleep(1)

    # MORT CHECKER
    async def on_voice_state_update(self, before, after):
        if before.voice_channel is None:
            ctx = after
        elif after.voice_channel is None:
            ctx = before

        if after.id == '342511480685461514':
            if (before.voice_channel is not None
            and after.voice_channel is None
            and before.voice_channel is not after.server.afk_channel
            and len(before.voice_channel.voice_members) >= 0 # CHANGE TO >
            or after.voice_channel is after.server.afk_channel
            and before.voice_channel is not None):

                self.vote_type = 'mort_checker'
                await self.vote_start(ctx, self.vote_type)

            else:
                mort_table =  bot.db['mort_checker']
                mort_shame_count = mort_table.find_one(name='mort')['mort_checker_count']
                mort_table.upsert(dict(name='mort', mort_checker_count=mort_shame_count), ['name'])
                mort_user = self.bot.get_server('299756881004462081').get_member('363303204546674688')
                mort_new_user = mort_user.nick.split('(')[0].strip()
                await self.bot.change_nickname(mort_user, '{} ({})'.format(mort_new_user, mort_shame_count))


def setup(bot):
    bot.add_cog(MortChecker(bot))
