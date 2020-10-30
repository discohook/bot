import re

import discord
from discord.ext import commands
from discord.utils import find, get

from . import wrap_in_code


class MessageConverter(commands.MessageConverter):
    """Converts to a :class:`discord.Message`.

    Different from `discord.ext.commands.converter.MessageConverter` by not
    leaking messages from other guilds, or channels the member cannot read.
    """

    async def convert(self, ctx: commands.Context, argument):
        message = await super().convert(ctx, argument)

        perms = message.channel.permissions_for(ctx.author)
        if (
            message.guild == ctx.guild
            and perms.read_messages
            and perms.read_message_history
        ):
            return message

        raise commands.ChannelNotReadable(message.channel)


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
