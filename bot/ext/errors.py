import sys
import traceback

import discord
from bot.utils import wrap_in_code
from discord.ext import commands

ignored_errors = (
    commands.CommandNotFound,
    commands.DisabledCommand,
    commands.NotOwner,
)

error_types = (
    (commands.CommandOnCooldown, "Cooldown"),
    (commands.UserInputError, "Bad input"),
    (commands.CheckFailure, "Check failed"),
)


class Errors(commands.Cog):
    """Error handlers"""

    def __init__(self, bot):
        self.bot = bot

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
    async def on_command_error(self, ctx: commands.Context, error):
        error = getattr(error, "original", error)

        if isinstance(error, ignored_errors):
            return

        for (error_type, error_msg) in error_types:
            if isinstance(error, error_type):
                await ctx.send(
                    embed=discord.Embed(title=error_msg, description=str(error)),
                )
                return

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
