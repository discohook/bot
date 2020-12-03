import math
import re
import sys
import traceback
import typing

import discord
from bot import cmd
from bot.utils import wrap_in_code
from discord.ext import commands
from discord.utils import escape_markdown

ignored_errors = [
    commands.CommandNotFound,
    commands.DisabledCommand,
    commands.NotOwner,
]


def humanize_perm(permission):
    return permission.replace("_", " ").replace("guild", "server").title()


bad_arg_converter_re = re.compile(r'Converting to "(.+)" failed for parameter "\w+".')

bad_arg_converter_messages = {
    "int": {
        "title": "Not a number",
        "description": "The argument could not be converted to an integer value.",
    },
}


def get_bad_arg_message(error: commands.BadArgument):
    match = bad_arg_converter_re.fullmatch(str(error))
    if match:
        converter_str = match.group(1)
        if converter_str in bad_arg_converter_messages:
            return bad_arg_converter_messages[converter_str]

    return {
        "title": "Bad argument",
        "description": "An argument you provided was invalid or not found, please read help for more info.",
    }


error_types = [
    (
        commands.MissingRequiredArgument,
        "Missing argument",
        lambda e: f"The {wrap_in_code(e.param.name)} argument is required, please read help for more info.",
    ),
    (
        commands.TooManyArguments,
        "Too many arguments",
        "Too many arguments were provided, please read help for more info.",
    ),
    (
        commands.MessageNotFound,
        "Message not found",
        lambda e: f"Could not find message for {wrap_in_code(e.argument)}.",
    ),
    (
        commands.MemberNotFound,
        "Member not found",
        lambda e: f"Could not find member for {wrap_in_code(e.argument)}.",
    ),
    (
        commands.UserNotFound,
        "User not found",
        lambda e: f"Could not find user for {wrap_in_code(e.argument)}.",
    ),
    (
        commands.ChannelNotFound,
        "Channel not found",
        lambda e: f"Could not find channel for {wrap_in_code(e.argument)}.",
    ),
    (
        (commands.EmojiNotFound, commands.PartialEmojiConversionFailure),
        "Emoji not found",
        lambda e: f"Could not find emoji for {wrap_in_code(e.argument)}.",
    ),
    (
        commands.ChannelNotReadable,
        "Channel not readable",
        lambda e: f"Could not read messages in {e.argument.mention}.",
    ),
    (
        commands.RoleNotFound,
        "Role not found",
        lambda e: f"Could not find role for {wrap_in_code(e.argument)}.",
    ),
    (
        commands.BadBoolArgument,
        "Not a boolean value",
        lambda e: f"Argument {wrap_in_code(e.argument)} is not a yes or no value.",
    ),
    (
        commands.BadArgument,
        lambda e: get_bad_arg_message(e)["title"],
        lambda e: get_bad_arg_message(e)["description"],
    ),
    (
        commands.ArgumentParsingError,
        "Argument parsing failed",
        "Failed to parse arguments, please check for quote marks.",
    ),
    (
        commands.UserInputError,
        "Bad user input",
        "Details are unknown, please read help for more info.",
    ),
    (
        commands.MissingPermissions,
        "Missing permissions",
        lambda e: f"You are missing permissions: {', '.join(humanize_perm(perm) for perm in e.missing_perms)}.",
    ),
    (
        commands.BotMissingPermissions,
        "Missing permissions",
        lambda e: f"I am missing permissions: {', '.join(humanize_perm(perm) for perm in e.missing_perms)}.",
    ),
    (
        commands.PrivateMessageOnly,
        "Invalid context",
        "This command can only be used in DMs",
    ),
    (
        commands.NoPrivateMessage,
        "Invalid context",
        "This command can only be used in servers",
    ),
    (
        commands.CheckFailure,
        "Check failure",
        "A condition failed, please read help for more info.",
    ),
    (
        commands.CommandOnCooldown,
        "Cooldown",
        lambda e: f"You're on cooldown, you can use this command again in {math.ceil(e.retry_after)} {'second' if math.ceil(e.retry_after) == 1 else 'seconds'}.",
    ),
    (
        commands.MaxConcurrencyReached,
        "Command already running",
        lambda e: f"This command is at its maximum capacity, please wait for any commands to finish.",
    ),
]


def resolve_value(maybe_callable, error):
    if callable(maybe_callable):
        return maybe_callable(error)
    return maybe_callable


class Errors(cmd.Cog):
    """Error handlers"""

    async def report_error(self, error, *, fields):
        exception = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

        print(exception, file=sys.stderr)

        embed = discord.Embed(
            title="Unhandled error", description=wrap_in_code(exception, block="py")
        )
        for field in fields:
            embed.add_field(**field)

        info = await self.bot.application_info()
        await info.owner.send(embed=embed)

    async def on_error(self, event, *args, **kwargs):
        error = sys.exc_info()[1]

        await self.report_error(
            error,
            fields=[
                {
                    "name": "Event",
                    "value": f"```{event}```",
                    "inline": False,
                },
                *(
                    {
                        "name": f"args[{index!r}]",
                        "value": wrap_in_code(repr(arg), block=True),
                        "inline": False,
                    }
                    for index, arg in enumerate(args)
                ),
                *(
                    {
                        "name": f"kwargs[{index!r}]",
                        "value": wrap_in_code(repr(arg), block=True),
                        "inline": False,
                    }
                    for index, arg in kwargs.items()
                ),
            ],
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx: cmd.Context, error):
        if str(error).startswith("The global check "):
            try:
                await self.bot.global_check(ctx)
            except commands.CommandError as exc:
                error = exc

        error = getattr(error, "original", error)

        if isinstance(error, tuple(ignored_errors)):
            return

        if isinstance(error, commands.BotMissingPermissions):
            if "send_messages" in error.missing_perms:
                try:
                    await ctx.author.send(
                        embed=discord.Embed(
                            title="Missing permissions",
                            description="Hey, I don't have permission to send messages"
                            f" in {wrap_in_code(ctx.guild.name)}, {ctx.channel.mention}."
                            "\nIf you think this is an error, please notify a server"
                            " administrator about this.",
                        )
                    )
                except discord.HTTPException:
                    pass
                return
            if (
                "embed_links" in error.missing_perms
                or "attach_files" in error.missing_perms
            ):
                await ctx.send(
                    "I don't have permission to embed links or attach files"
                    " in this channel. Please notify an administrator about"
                    " this.",
                )
                return

        if isinstance(error, commands.BadUnionArgument):
            embed = discord.Embed(
                title="Could not convert argument",
                description="Multiple types of values are accepted, individual errors can be found below.",
            )

            for error in error.errors:
                for error_type, title, description in error_types:
                    if isinstance(error, error_type):
                        embed.add_field(
                            name=resolve_value(title, error),
                            value=resolve_value(description, error),
                            inline=False,
                        )

                        break

            await ctx.send(embed=embed)
            return

        for error_type, title, description in error_types:
            if isinstance(error, error_type):
                await ctx.send(
                    embed=discord.Embed(
                        title=resolve_value(title, error),
                        description=resolve_value(description, error),
                    ),
                )

                return

        await ctx.send(
            embed=discord.Embed(
                title="Error",
                description="An unknown error has occured, please report this.",
            )
        )

        await self.report_error(
            error,
            fields=[
                {
                    "name": "Message",
                    "value": ctx.message.content,
                    "inline": False,
                },
            ],
        )


def setup(bot):
    bot.add_cog(Errors(bot))
