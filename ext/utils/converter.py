import re

import discord
from discord.ext import commands
from discord.utils import find, get

from . import wrap_in_code


class GuildMemberConverter(commands.IDConverter):
    """Converts to a :class:`discord.Member`.
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

        argument = argument.strip()

        match = self._get_id_match(argument) or re.match(r"<@!?([0-9]+)>$", argument)
        result = None

        if match:
            user_id = int(match.group(1))

            result = get(
                ctx.message.mentions, id=user_id
            ) or await ctx.guild.fetch_member(user_id)

            if result:
                return result

        async for member in ctx.guild.fetch_members(limit=None):
            if len(argument) > 5 and argument[-5] == "#":
                if (
                    member.name == argument[:-5]
                    and member.discriminator == argument[-4:]
                ):
                    return member

            if member.name == argument or member.nick == argument:
                return member

        raise commands.BadArgument(f"Member {wrap_in_code(argument)} not found")


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

        argument = argument.strip()

        match = self._get_id_match(argument) or re.match(r"<@&([0-9]+)>$", argument)

        if match:
            result = ctx.guild.get_role(int(match.group(1)))
        else:
            result = discord.utils.get(ctx.guild._roles.values(), name=argument)

        if result is None:
            raise commands.BadArgument(f"Role {wrap_in_code(argument)} not found")

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

        argument = argument.strip()

        match = self._get_id_match(argument) or re.match(r"<#([0-9]+)>$", argument)
        result = None

        if match is None:
            result = discord.utils.get(ctx.guild.text_channels, name=argument)
        else:
            channel_id = int(match.group(1))
            result = ctx.guild.get_channel(channel_id)

        if not isinstance(result, discord.TextChannel):
            raise commands.BadArgument(f"Channel {wrap_in_code(argument)} not found")

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

        argument = argument.strip()

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
            raise commands.BadArgument(f"Emoji {wrap_in_code(argument)} not found")

        return result


class GuildPartialEmojiConverter(commands.Converter):
    """Converts to a :class:`discord.PartialEmoji`.
    This is done by extracting the animated flag, name and ID from the emoji.
    If it's not an emoji string, it does a lookup by name.
    """

    async def convert(self, ctx, argument):
        match = re.match(r"<(a?):([a-zA-Z0-9\_]+):([0-9]+)>$", argument)

        if match:
            emoji_animated = bool(match.group(1))
            emoji_name = match.group(2)
            emoji_id = int(match.group(3))

            return discord.PartialEmoji.with_state(
                ctx.bot._connection,
                id=emoji_id,
                name=emoji_name,
                animated=emoji_animated,
            )

        emoji = discord.utils.get(ctx.guild.emojis, name=argument)
        if emoji:
            return discord.PartialEmoji.with_state(
                ctx.bot._connection,
                id=emoji.id,
                name=emoji.name,
                animated=emoji.animated,
            )

        raise commands.BadArgument(f"Emoji {wrap_in_code(argument)} not found")


class GuildMessageConverter(commands.Converter):
    """Converts to a :class:`discord.Message`.
    The lookup strategy is as follows (in order):
    1. Lookup by "{channel ID}-{message ID}" (retrieved by shift-clicking on "Copy ID")
    2. Lookup by message ID (the message **must** be in the context channel)
    3. Lookup by message URL
    """

    async def convert(self, ctx: commands.Context, argument):
        if not ctx.guild:
            raise commands.NoPrivateMessage()

        argument = argument.strip()

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
            raise commands.BadArgument(f"Message {wrap_in_code(argument)} not found")

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
                raise commands.BadArgument(
                    f"Message {wrap_in_code(argument)} not found"
                )

        channel = ctx.bot.get_channel(int(channel_id)) if channel_id else ctx.channel
        if not channel:
            raise commands.BadArgument(f"Message {wrap_in_code(argument)} not found")

        try:
            message = await channel.fetch_message(message_id)
            if (
                message.guild == ctx.guild
                and message.channel.permissions_for(ctx.author).read_messages
                and message.channel.permissions_for(ctx.author).read_message_history
            ):
                return message
            else:
                raise commands.BadArgument(
                    f"Message {wrap_in_code(argument)} not found"
                )
        except discord.NotFound:
            raise commands.BadArgument(f"Message {wrap_in_code(argument)} not found")
        except discord.Forbidden:
            raise commands.BadArgument(f"Message {wrap_in_code(argument)} not found")


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
