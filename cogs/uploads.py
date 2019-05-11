import discord
import asyncio
import bot
import requests
import boto3
from discord.ext import commands


class Uploads:
    def __init__(self, bot):
        self.bot = bot
        self.bot_id = "471255864238538753"

    async def on_message(self, message):
        import pdb;pdb.set_trace()
        if message.channel.id != "574866821061017600":
            return

        try:
            file_name = message.attachments[0]["filename"] or None
        except IndexError:
            if message.author.id != self.bot_id:
                await self.bot.delete_message(message)
            return
        # upload-sounds text channel
        if file_name.endswith(".mp3"):
            request = requests.get(message.attachments[0]["url"], stream=True)
            session = boto3.Session(
                aws_access_key_id=bot.config["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=bot.config["AWS_SECRET_ACCESS_KEY"],
            )
            s3 = session.resource("s3")
            bucket = s3.Bucket(bot.config["AWS_STORAGE_BUCKET_NAME"])
            bucket.upload_fileobj(request.raw, file_name)

            if message.author.id != self.bot_id:
                await self.bot.delete_message(message)
            await self.bot.send_message(
                message.channel, "{} has been uploaded.".format(file_name)
            )


def setup(bot):
    bot.add_cog(Uploads(bot))
