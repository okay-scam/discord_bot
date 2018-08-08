import discord
import asyncio
import math
import bot
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
        self.voice_members_count = len(ctx.message.author.voice_channel.voice_members)
        self.vote_threshold = math.ceil((self.voice_members_count * (self.vote_threshold_percentage/100))+1) # +1 to account for bots initial "votes"
        self.server = ctx.message.server

        # Check if that user is in your channel
        # CAN WE REPLACE THIS WITH A @CHECK?
        voice_channel_members = ctx.message.author.voice_channel.voice_members
        if self.mentioned_user not in voice_channel_members:
            await self.bot.say('```User must be in your voice channel to start a vote```')
            return

        # Then, we check if there are enough people in the channel to start a vote (min = 2)
        if self.voice_members_count < 2:
            await self.bot.say('```Minimum of 2 users are required in a voice channel to start a vote.```')
            return
        
        # Then, we check is vote is already in progress
        # CAN WE REPLACE THIS WITH A @CHECK?
        if self.vote_in_progress:
            await self.bot.say('Vote in progress, please wait...')
            return
        
        # Build vote message embed object
        if self.vote_type == 'mute':
            vote_type_string = 'mute'
        elif self.vote_type == 'enforce_ptt':
            vote_type_string = 'enforce push-to-talk for'
        else:
            self.bot.say('```Error: Unknown vote type```')
            return
            
        self.embed = discord.Embed(colour=discord.Colour(0xff0000))
        self.embed.description = '{0} wants to {1} {2}\n\n{3}'.format(ctx.message.author.mention, vote_type_string, self.mentioned_user.mention, '**Vote now!**')
        self.embed.set_footer(text='{} or more ✅ to pass!'.format(self.vote_threshold))
        self.embed.add_field(name=':white_check_mark:', value='Yes', inline=True)
        self.embed.add_field(name=':x:', value='No', inline=True)

        # Send vote embed & set vote state
        self.vote_in_progress = True
        self.vote = await self.bot.say(embed=self.embed)
        # Add reacts to vote message
        await self.bot.add_reaction(self.vote, '✅')
        await self.bot.add_reaction(self.vote, '❌')

        # Update current voter ids list
        await self.update_voter_ids()        

        # Vote timeout
        await asyncio.sleep(30)
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
            if self.vote_type == 'mute':
                await self.mute_user(self.mentioned_user)
            if self.vote_type == 'enforce_ptt':
                user_permissions = await self.get_user_permissions(self.mentioned_user)
                user_has_voice_act = await self.permissions_has_voice_act(user_permissions)
                if user_has_voice_act:
                    voice_act_roles = await self.get_voice_act_roles(user_permissions)
                    voice_act_role_objs = await self.get_roles(voice_act_roles)
                    await self.bot.remove_roles(self.mentioned_user, *voice_act_role_objs)
        return

    async def get_roles(self, target_names):
        # Pass me a list of role names and I'll return their role objects as a list
        server_roles = self.server.roles
        return_roles = []

        for target in target_names:
            for role in server_roles:
                if role.name == target:
                    return_roles.append(role)
        return return_roles

    async def mute_user(self, user):
        await self.bot.server_voice_state(user, mute=True)

    async def get_user_permissions(self, user: discord.User):
        # Returns a dict of role: [permissions]
        # eg. "@everyone": {[('use_voice_activation','true'), ('kick_members', false)]}
        user_permissions = {}
        for role in user.roles:
            user_permissions[role.name] = dict(role.permissions)
        return user_permissions

    async def permissions_has_voice_act(self, user_permissions):
        # Use get_user_permissions to pass into user_permissions
        # user_permissions should be a dict

        # Returns true if user has voice_act permissions from any of their roles
        return any([y['use_voice_activation'] for x, y in user_permissions.items()])

    async def get_voice_act_roles(self, user_permissions):
        # Returns all role objects where use_voice_activation == True
        return ([x for x, y in user_permissions.items() if y['use_voice_activation'] == True])

## COMMANDS
    @commands.command(pass_context=True)
    async def vm(self, ctx, user: discord.User):
        self.vote_type = 'mute'

        # Get mentioned user
        self.mentioned_user = user
        await self.vote_start(ctx, self.vote_type)

    @commands.command()
    @commands.has_role('CEO')
    async def vend(self):
        if self.vote_in_progress:
            await self.vote_end('force_end')
        return

    @commands.command(pass_context=True)
    async def vptt(self, ctx, user: discord.User):
        self.vote_type = 'enforce_ptt'

        # Get mentioned user
        self.mentioned_user = user
        await self.vote_start(ctx, self.vote_type)    

    # On react adds  
    async def on_reaction_add(self, reaction, user):
        # Ignore to bot reacts
        if user.id == self.bot.user.id:
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


def setup(bot):
    bot.add_cog(Votes(bot))