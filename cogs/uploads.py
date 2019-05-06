import discord
import asyncio
import bot
import requests
import boto3
from boto.s3.connection import S3Connection
from discord.ext import commands


class Uploads():
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        # upload-sounds text channel
        if message.channel.id == '574866821061017600':
            if message.attachments[0]['filename'].endswith('.mp3'):
                conn = S3Connection(bot.config['AWS_ACCESS_KEY_ID'], bot.config['AWS_SECRET_ACCESS_KEY'])
                bucket = conn.get_bucket(bot.config['AWS_STORAGE_BUCKET_NAME'])

                url = message.attachments[0]['url']
                re = requests.get(url, stream=True)

                session = boto3.Session(aws_access_key_id=bot.config['AWS_ACCESS_KEY_ID'], aws_secret_access_key=bot.config['AWS_SECRET_ACCESS_KEY'])
                s3 = session.resource('s3')

                bucket = s3.Bucket(bot.config['AWS_STORAGE_BUCKET_NAME'])
                bucket.upload_fileobj(re.raw, message.attachments[0]['filename'])


def setup(bot):
    bot.add_cog(Uploads(bot))
