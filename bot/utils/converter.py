import re

import discord
from discord.ext import commands
from discord.utils import find, get

from . import wrap_in_code


class MessageConverter(commands.Converter):
    """Converts to a :class:`discord.Message`.

    Different from `discord.ext.commands.converter.MessageConverter` by not
    leaking messages from other guilds, or channels the member cannot read.
    """

    def readable_by_member(self, ctx: commands.Context, message: discord.Message):
        return (
            message.guild == ctx.guild
            and message.channel.permissions_for(ctx.author).read_messages
            and message.channel.permissions_for(ctx.author).read_message_history
        )

    async def convert(self, ctx: commands.Context, argument):
        id_regex = re.compile(
            r"^(?:(?P<channel_id>[0-9]{15,21})-)?(?P<message_id>[0-9]{15,21})$"
        )
        link_regex = re.compile(
            r"^https?://(?:(ptb|canary)\.)?discord(?:app)?\.com/channels/"
            r"(?:([0-9]{15,21})|(@me))"
            r"/(?P<channel_id>[0-9]{15,21})/(?P<message_id>[0-9]{15,21})/?$"
        )

        match = id_regex.match(argument) or link_regex.match(argument)
        if not match:
            raise commands.MessageNotFound(argument)

        message_id = int(match.group("message_id"))
        channel_id = int(match.group("channel_id") or 0)

        message = ctx.bot._connection._get_message(message_id)
        if message:
            if self.readable_by_member(ctx, message):
                return message

            raise commands.ChannelNotReadable(message.channel)

        channel = ctx.bot.get_channel(channel_id) if channel_id else ctx.channel
        if not channel:
            raise commands.ChannelNotFound(str(channel_id))

        try:
            message = await channel.fetch_message(message_id)
            if self.readable_by_member(ctx, message):
                return message

            raise commands.ChannelNotReadable(channel)
        except discord.NotFound:
            raise commands.MessageNotFound(argument)
        except discord.Forbidden:
            raise commands.ChannelNotReadable(channel)


class WebhookConverter(commands.IDConverter):
    """Converts to a :class:`discord.Webhook`.
    The lookup strategy is as follows (in order):
    1. Lookup by webhook ID
    2. Lookup by name in current channel
    3. Lookup by name in current guild
    """

    async def convert(self, ctx: commands.Context, argument: str):
        if not ctx.guild:
            raise commands.NoPrivateMessage()

        argument = argument.strip()

        match = self._get_id_match(argument)

        webhooks = [
            webhook
            for webhook in await ctx.guild.webhooks()
            if webhook.type == discord.WebhookType.incoming
        ]

        result = None
        if match:
            result = discord.utils.get(webhooks, id=int(match.group(1)))
        if result is None:
            result = discord.utils.get(
                webhooks, channel_id=ctx.channel.id, name=argument
            )
        if result is None:
            result = discord.utils.get(webhooks, name=argument)

        if result is None:
            raise commands.BadArgument(f"Webhook {wrap_in_code(argument)} not found")

        return result
