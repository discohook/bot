import re

import discord
from discord.ext import commands


class GuildMemberConverter(commands.IDConverter):
    """Converts to a :class:`~discord.Member`.
    All lookups are via the local guild.
    The lookup strategy is as follows (in order):
    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name#discrim
    4. Lookup by name
    5. Lookup by nickname
    """

    async def convert(self, ctx, argument):
        if not ctx.guild:
            raise commands.NoPrivateMessage()

        match = self._get_id_match(argument) or re.match(r"<@!?([0-9]+)>$", argument)
        result = None

        if match is None:
            result = ctx.guild.get_member_named(argument)

        else:
            user_id = int(match.group(1))
            result = ctx.guild.get_member(user_id) or discord.utils.get(
                ctx.message.mentions, id=user_id
            )

        if result is None:
            raise commands.BadArgument(f'Member "{argument}" not found')

        return result


class GuildRoleConverter(commands.IDConverter):
    """Converts to a :class:`discord.Role`.
    All lookups are via the local guild.
    The lookup strategy is as follows (in order):
    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name
    """

    async def convert(self, ctx, argument):
        if not ctx.guild:
            raise commands.NoPrivateMessage()

        match = self._get_id_match(argument) or re.match(r"<@&([0-9]+)>$", argument)

        if match:
            result = ctx.guild.get_role(int(match.group(1)))
        else:
            result = discord.utils.get(ctx.guild._roles.values(), name=argument)

        if result is None:
            raise commands.BadArgument(f'Role "{argument}" not found')

        return result


class GuildTextChannelConverter(commands.IDConverter):
    """Converts to a :class:`discord.TextChannel`.
    All lookups are via the local guild.
    The lookup strategy is as follows (in order):
    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name
    """

    async def convert(self, ctx, argument):
        if not ctx.guild:
            raise commands.NoPrivateMessage()

        match = self._get_id_match(argument) or re.match(r"<#([0-9]+)>$", argument)
        result = None

        if match is None:
            result = discord.utils.get(ctx.guild.text_channels, name=argument)
        else:
            channel_id = int(match.group(1))
            result = ctx.guild.get_channel(channel_id)

        if not isinstance(result, discord.TextChannel):
            raise commands.BadArgument(f'Channel "{argument}" not found')

        return result


class GuildEmojiConverter(commands.IDConverter):
    """Converts to a :class:`discord.Emoji`.
    All lookups are done for the local guild, if available.
    The lookup strategy is as follows (in order):
    1. Lookup by ID.
    2. Lookup by extracting ID from the emoji.
    3. Lookup by name
    """

    async def convert(self, ctx, argument):
        if not ctx.guild:
            raise commands.NoPrivateMessage()

        match = self._get_id_match(argument) or re.match(
            r"<a?:[a-zA-Z0-9\_]+:([0-9]+)>$", argument
        )
        result = None

        if match is None:
            result = discord.utils.get(ctx.guild.emojis, name=argument)
        else:
            emoji_id = int(match.group(1))
            result = discord.utils.get(ctx.guild.emojis, id=emoji_id)

        if result is None:
            raise commands.BadArgument(f'Emoji "{argument}" not found')

        return result


class GuildMessageConverter(commands.Converter):
    """Converts to a :class:`discord.Message`.
    The lookup strategy is as follows (in order):
    1. Lookup by "{channel ID}-{message ID}" (retrieved by shift-clicking on "Copy ID")
    2. Lookup by message ID (the message **must** be in the context channel)
    3. Lookup by message URL
    """

    async def convert(self, ctx: commands.Context, argument: str):
        if not ctx.guild:
            raise commands.NoPrivateMessage()

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
            raise commands.BadArgument(f'Message "{argument}" not found')

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
                raise commands.BadArgument(f'Message "{argument}" not found')

        channel = ctx.bot.get_channel(int(channel_id)) if channel_id else ctx.channel
        if not channel:
            raise commands.BadArgument(f'Message "{argument}" not found')

        try:
            message = await channel.fetch_message(message_id)
            if (
                message.guild == ctx.guild
                and message.channel.permissions_for(ctx.author).read_messages
                and message.channel.permissions_for(ctx.author).read_message_history
            ):
                return message
            else:
                raise commands.BadArgument(f'Message "{argument}" not found')
        except discord.NotFound:
            raise commands.BadArgument(f'Message "{argument}" not found')
        except discord.Forbidden:
            raise commands.BadArgument(f'Message "{argument}" not found')
