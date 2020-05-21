import re

import discord
from discord.ext import commands


class MessageConverter(commands.Converter):
    """Converts to a :class:`discord.Message`.
    The lookup strategy is as follows (in order):
    1. Lookup by "{channel ID}-{message ID}" (retrieved by shift-clicking on "Copy ID")
    2. Lookup by message ID (the message **must** be in the context channel)
    3. Lookup by message URL
    """

    async def convert(self, ctx: commands.Context, argument: str):
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
            raise commands.BadArgument(f'Message "{argument}" not found.')

        message_id = int(match.group("message_id"))
        channel_id = match.group("channel_id")
        message = ctx.bot._connection._get_message(message_id)

        if message:
            if (
                message.guild == ctx.guild
                and message.channel.permissions_for(ctx.author).read_messages
                and message.channel.permissions_for(ctx.author).read_message_history
            ):
                return message
            else:
                raise commands.BadArgument(f'Message "{argument}" not found.')

        channel = ctx.bot.get_channel(int(channel_id)) if channel_id else ctx.channel
        if not channel:
            raise commands.BadArgument(f'Channel "{channel_id}" not found.')

        try:
            message = await channel.fetch_message(message_id)
            if (
                message.guild == ctx.guild
                and message.channel.permissions_for(ctx.author).read_messages
                and message.channel.permissions_for(ctx.author).read_message_history
            ):
                return message
            else:
                raise commands.BadArgument(f'Message "{argument}" not found.')
        except discord.NotFound:
            raise commands.BadArgument(f'Message "{argument}" not found.')
        except discord.Forbidden:
            raise commands.BadArgument(f"Can't read messages in {channel.mention}")
