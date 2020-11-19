import base64
import json
from datetime import datetime
from os import environ

import discord
from bot import checks, cmd, converter
from discord.ext import commands


class Utilities(cmd.Cog):
    """Message helpers"""

    async def get_short_url(self, url):
        async with self.session.post(
            "https://share.discohook.app/create", json={"url": url}
        ) as resp:
            if not resp.ok:
                return None, None

            data = await resp.json()
            url = data["url"]
            expires = datetime.strptime(data["expires"], "%Y-%m-%dT%H:%M:%S.%f")

            return url, expires

    @commands.command()
    @commands.cooldown(3, 30, type=commands.BucketType.user)
    @checks.sensitive()
    async def link(self, ctx: cmd.Context, message: converter.MessageConverter):
        """Sends a link to recreate a given message in Discohook by message link"""

        message_data = {}

        if len(message.content) > 0:
            message_data["content"] = message.content

        embeds = [embed.to_dict() for embed in message.embeds if embed.type == "rich"]

        for embed in embeds:
            embed.pop("type")

        if len(embeds) > 0:
            message_data["embeds"] = embeds

        message_json = json.dumps({"message": message_data}, separators=(",", ":"))
        message_b64 = (
            base64.urlsafe_b64encode(message_json.encode("utf-8"))
            .decode("utf-8")
            .replace("=", "")
        )
        url = f"https://discohook.app/?message={message_b64}"

        short_url, timestamp = await self.get_short_url(url)

        if short_url is None:
            await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Failed to get short URL",
                )
            )
            return

        embed = discord.Embed(
            title="Message",
            description=short_url,
        )
        embed.set_footer(text="Expires")
        embed.timestamp = timestamp
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(4, 4, commands.BucketType.member)
    async def big(self, ctx: cmd.Context, *, emoji: converter.PartialEmojiConverter):
        """Gives the URL to a custom emoji"""

        embed = discord.Embed(
            title=f"Emoji URL for :{emoji.name}:", description=str(emoji.url)
        )
        embed.set_image(url=str(emoji.url))
        embed.set_footer(text=f"ID: {emoji.id}")

        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    @commands.cooldown(4, 4, commands.BucketType.member)
    async def avatar(self, ctx: cmd.Context, *, user: discord.User = None):
        """Gives the URL to a user's avatar"""

        if not user:
            user = ctx.author

        url = str(user.avatar_url_as(static_format="png", size=4096))

        embed = discord.Embed(title=f"Avatar URL for @{user}", description=url)
        embed.set_image(url=url)
        embed.set_footer(text=f"ID: {user.id}")

        await ctx.send(embed=embed)

    @avatar.command(name="static")
    @commands.cooldown(4, 4, commands.BucketType.member)
    async def avatar_static(self, ctx: cmd.Context, *, user: discord.User = None):
        """Gives the URL to a user's non-animated avatar"""

        if not user:
            user = ctx.author

        url = str(user.avatar_url_as(format="png", size=4096))

        embed = discord.Embed(title=f"Avatar URL for @{user}", description=url)
        embed.set_image(url=url)
        embed.set_footer(text=f"ID: {user.id}")

        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    @commands.cooldown(4, 4, commands.BucketType.member)
    async def icon(self, ctx: cmd.Context):
        """Gives the URL to the server's icon"""

        url = str(ctx.guild.icon_url_as(static_format="png", size=4096))

        embed = discord.Embed(title=f"Icon URL for {ctx.guild}", description=url)
        embed.set_image(url=url)
        embed.set_footer(text=f"ID: {ctx.guild.id}")

        await ctx.send(embed=embed)

    @icon.command(name="static")
    @commands.cooldown(4, 4, commands.BucketType.member)
    async def icon_static(self, ctx: cmd.Context):
        """Gives the URL to the server's non-animated icon"""

        url = str(ctx.guild.icon_url_as(format="png", size=4096))

        embed = discord.Embed(title=f"Icon URL for {ctx.guild}", description=url)
        embed.set_image(url=url)
        embed.set_footer(text=f"ID: {ctx.guild.id}")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Utilities(bot))
