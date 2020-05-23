import sys
import traceback
from os import environ

import discord
from discord.ext import commands

extensions = (
    "ext.markdown",
    "ext.messages",
)

error_types = (
    (commands.UserInputError, "Bad input"),
    (commands.CheckFailure, "Check failed"),
)


def _prefix(bot, msg):
    prefixes = (f"<@!{bot.user.id}> ", f"<@{bot.user.id}> ")
    prefixes = (*prefixes, "d.", "d!")

    return prefixes


class Bot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=_prefix,
            description="Helper bot for Discohook <https://discohook.org/>",
            activity=discord.Game(name="at discohook.org | d.help"),
        )

        for extension in extensions:
            self.load_extension(extension)

    async def on_ready(self):
        print(f"Ready as {self.user} ({self.user.id})")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        for (error_type, error_msg) in error_types:
            if isinstance(error, error_type):
                await ctx.send(
                    embed=discord.Embed(title=error_msg, description=str(error))
                )
                return

        err = error
        if isinstance(error, commands.CommandInvokeError):
            err = error.original

        if not isinstance(err, discord.HTTPException):
            traceback.print_tb(err.__traceback__)
            print(f"{err.__class__.__name__}: {err}", file=sys.stderr)


def main():
    bot = Bot()
    bot.run(environ.get("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()
