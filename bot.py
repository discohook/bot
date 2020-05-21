import sys
import traceback
from os import environ

import discord
from discord.ext import commands

extensions = (
    "ext.markdown",
    "ext.messages",
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
        if isinstance(error, commands.UserInputError) or isinstance(
            error, commands.CheckFailure
        ):
            await ctx.send(error)

        elif isinstance(error, commands.CommandNotFound):
            pass

        else:
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
