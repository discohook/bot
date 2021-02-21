import base64
import json
from datetime import datetime
from os import environ
from urllib.parse import urlunparse

import discord
from bot import checks, cmd, converter
from discord.ext import commands


class Utilities(cmd.Cog):
    """Message helpers"""

    async def get_short_url(self, url):
        async with self.session.post(
            "https://share.discohook.app/create", json={"url": url}
        ) as resp:
            if resp.status >= 400:
                return None, None

            data = await resp.json()
            url = data["url"]
            expires = datetime.fromisoformat(data["expires"])

            return url, expires

    def get_message_data(self, message: discord.Message):
        data = {
            "content": message.content,
            "embeds": [],
        }

        for embed in message.embeds:
            if embed.type != "rich":
                continue

            embed_dict = embed.to_dict()
            embed_dict.pop("type")
            data["embeds"].append(embed_dict)

        if len(data["embeds"]) <= 0:
            data.pop("embeds")

        return data

    @commands.group(invoke_without_command=True, require_var_positional=True)
    @commands.cooldown(3, 30, type=commands.BucketType.user)
    @checks.sensitive()
    async def link(self, ctx: cmd.Context, *messages: converter.MessageConverter):
        """Sends a link to recreate a given message in Discohook by message link"""

        data = {"messages": []}
        for message in messages:
            data["messages"].append(
                {
                    "data": self.get_message_data(message),
                }
            )

        data_json = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        data_b64 = base64.urlsafe_b64encode(data_json.encode()).decode().strip("=")
        url = urlunparse(("https", "discohook.app", "/", "", f"data={data_b64}", ""))

        short_url, timestamp = await self.get_short_url(url)

        if short_url is None:
            await ctx.prompt(
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
        await ctx.prompt(embed=embed)

    @link.command(name="edit", require_var_positional=True)
    @commands.cooldown(3, 30, type=commands.BucketType.user)
    @checks.sensitive()
    async def link_edit(self, ctx: cmd.Context, *messages: converter.MessageConverter):
        """Sends a link to recreate a given message in Discohook by message link"""

        data = {"messages": []}
        for message in messages:
            data["messages"].append(
                {
                    "data": self.get_message_data(message),
                    "reference": message.jump_url,
                }
            )

        data_json = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        data_b64 = base64.urlsafe_b64encode(data_json.encode()).decode().strip("=")
        url = urlunparse(("https", "discohook.app", "/", "", f"data={data_b64}", ""))

        short_url, timestamp = await self.get_short_url(url)

        if short_url is None:
            await ctx.prompt(
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
        await ctx.prompt(embed=embed)

    @commands.command()
    @commands.cooldown(4, 4, commands.BucketType.member)
    async def big(self, ctx: cmd.Context, *, emoji: converter.PartialEmojiConverter):
        """Gives the URL to a custom emoji"""

        embed = discord.Embed(
            title=f"Emoji URL for :{emoji.name}:", description=str(emoji.url)
        )
        embed.set_image(url=str(emoji.url))
        embed.set_footer(text=f"ID: {emoji.id}")

        await ctx.prompt(embed=embed)

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

        await ctx.prompt(embed=embed)

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

        await ctx.prompt(embed=embed)

    @commands.group(invoke_without_command=True)
    @commands.cooldown(4, 4, commands.BucketType.member)
    async def icon(self, ctx: cmd.Context):
        """Gives the URL to the server's icon"""

        url = str(ctx.guild.icon_url_as(static_format="png", size=4096))

        embed = discord.Embed(title=f"Icon URL for {ctx.guild}", description=url)
        embed.set_image(url=url)
        embed.set_footer(text=f"ID: {ctx.guild.id}")

        await ctx.prompt(embed=embed)

    @icon.command(name="static")
    @commands.cooldown(4, 4, commands.BucketType.member)
    async def icon_static(self, ctx: cmd.Context):
        """Gives the URL to the server's non-animated icon"""

        url = str(ctx.guild.icon_url_as(format="png", size=4096))

        embed = discord.Embed(title=f"Icon URL for {ctx.guild}", description=url)
        embed.set_image(url=url)
        embed.set_footer(text=f"ID: {ctx.guild.id}")

        await ctx.prompt(embed=embed)


def setup(bot):
    bot.add_cog(Utilities(bot))
