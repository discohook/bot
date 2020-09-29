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

        exception = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

        print(exception, file=sys.stderr)

        embed = discord.Embed(
            title="Unhandled error", description=wrap_in_code(exception, block="py")
        )
        embed.add_field(name="Original message", value=ctx.message.content)

        info = await self.bot.application_info()
        await info.owner.send(embed=embed)


def setup(bot):
    bot.add_cog(Errors(bot))
