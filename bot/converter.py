import discord
from discord.ext import commands
from discord.utils import get


class MessageConverter(commands.MessageConverter):
    """Converts to a :class:`discord.Message`.

    Different from `discord.ext.commands.converter.MessageConverter` by not
    leaking messages from other guilds, or channels the member cannot read.
    """

    async def convert(self, ctx: cmd.Context, argument):
        message = await super().convert(ctx, argument)

        perms = message.channel.permissions_for(ctx.author)
        if (
            message.guild == ctx.guild
            and perms.read_messages
            and perms.read_message_history
        ):
            return message

        raise commands.ChannelNotReadable(message.channel)


class PartialEmojiConverter(commands.PartialEmojiConverter):
    """Converts to a :class:`~discord.PartialEmoji`.

    Different from `discord.ext.commands.converter.PartialEmojiConverter` by
    falling back to getting emoji by name from the guild.
    """

    async def convert(self, ctx: cmd.Context, argument):
        try:
            return await super().convert(ctx, argument)
        except commands.PartialEmojiConversionFailure:
            if not ctx.guild:
                raise

            guild_emoji = get(ctx.guild.emojis, name=argument.strip(":"))
            if guild_emoji is None:
                guild_emoji = get(ctx.guild.emojis, id=argument)

            return await super().convert(ctx, str(guild_emoji or argument))


class WebhookConverter(commands.IDConverter):
    """Converts to a :class:`discord.Webhook`.
    The lookup strategy is as follows (in order):
    1. Lookup by webhook ID
    2. Lookup by name in current channel
    3. Lookup by name in current guild
    """

    async def convert(self, ctx: cmd.Context, argument: str):
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
            raise commands.BadArgument(f"Webhook {argument!r} not found")

        return result
