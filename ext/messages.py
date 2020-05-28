import base64
import io
import json

import discord
from discord.ext import commands

from .utils import converter


class Messages(commands.Cog):
    """Message helpers"""

    @commands.command()
    async def link(
        self, ctx: commands.Context, message: converter.GuildMessageConverter,
    ):
        """Sends a link to recreate a given message in Discohook by message link"""

        message_data = {}

        if len(message.content) > 0:
            message_data["content"] = message.content

        message_data["username"] = message.author.display_name
        message_data["avatar_url"] = str(message.author.avatar_url_as(format="webp"))

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
        url = f"https://discohook.org/?message={message_b64}"

        if len(url) > 512:
            await ctx.send(
                embed=discord.Embed(title="URL too long for embed"),
                file=discord.File(io.StringIO(url), filename="url.txt"),
            )
        else:
            await ctx.send(embed=discord.Embed(title="Message", url=url))


def setup(bot):
    bot.add_cog(Messages(bot))
