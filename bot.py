import asyncio
import re
import sys
import traceback
from os import environ

import aiohttp
import discord
from discord.ext import commands

from ext.utils import config

environ.setdefault("JISHAKU_HIDE", "true")

extensions = (
    "jishaku",
    "ext.markdown",
    "ext.messages",
    "ext.meta",
    "ext.webhooks",
)

error_types = [
    (commands.CommandOnCooldown, "Cooldown"),
    (commands.UserInputError, "Bad input"),
    (commands.CheckFailure, "Check failed"),
]


def _prefix(bot, msg):
    prefix = bot.prefixes.get(msg.guild.id if msg.guild else 0, "d.")

    return (
        f"<@!{bot.user.id}> ",
        f"<@{bot.user.id}> ",
        f"{prefix} ",
        prefix,
    )


class Bot(commands.AutoShardedBot):
    def __init__(self,):
        super().__init__(
            command_prefix=_prefix,
            description="Helper bot for Discohook (<https://discohook.org/>)"
            "\nNeed help? Ask in the [support server](https://discohook.org/discord)."
            "\nWant me in your server? [Invite me](https://discohook.org/bot).",
            activity=discord.Game(name="at discohook.org | d.help"),
        )

        self.prefixes = config.Config("prefixes.json")

    async def on_ready(self):
        self.session = aiohttp.ClientSession()

        for extension in extensions:
            self.load_extension(extension)

        print(f"Ready as {self.user} ({self.user.id})")

    async def close(self):
        await self.session.close()
        await super().close()

    async def on_message(self, message):
        if message.author.bot:
            return

        if re.fullmatch(rf"<@!?{self.user.id}>", message.content):
            description = 'The prefix for Discobot is "d."'

            if message.guild:
                prefix = self.prefixes.get(message.guild.id, "d.")
                description = f'The prefix for Discobot in this server is "{prefix}"'

            await message.channel.send(
                embed=discord.Embed(title="Prefix", description=description)
            )
            return

        await self.process_commands(message)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        for (error_type, error_msg) in error_types:
            if isinstance(error, error_type):
                await ctx.send(
                    embed=discord.Embed(title=error_msg, description=str(error)),
                    delete_after=10,
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
