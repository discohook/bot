import asyncio
import re
import sys
import traceback
from os import environ

import aiohttp
import asyncpg
import discord
from discord.ext import commands

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


async def _prefix(bot, msg):
    prefix = await bot.db.fetchval(
        """
        SELECT prefix FROM guild_config
        WHERE guild_id = $1
        """,
        msg.guild.id,
    )

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

    async def on_ready(self):
        self.db = await asyncpg.create_pool(dsn=environ.get("DATABASE_DSN"))
        self.session = aiohttp.ClientSession()

        for extension in extensions:
            self.load_extension(extension)

        print(f"Ready as {self.user} ({self.user.id})")

    async def close(self):
        await self.session.close()
        await self.db.close()
        await super().close()

    async def on_message(self, message):
        if message.author.bot:
            return

        if message.guild:
            async with self.db.acquire() as conn:
                try:
                    await self.db.execute(
                        """
                        INSERT INTO guild_config (guild_id)
                        VALUES ($1)
                        """,
                        message.guild.id,
                    )
                except asyncpg.UniqueViolationError:
                    pass

        if re.fullmatch(rf"<@!?{self.user.id}>", message.content):
            description = 'The prefix for Discobot is "d."'

            if message.guild:
                prefix = await self.db.fetchval(
                    """
                    SELECT prefix FROM guild_config
                    WHERE guild_id = $1
                    """,
                    message.guild.id,
                )
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

    async def on_guild_remove(self, guild):
        await self.db.execute(
            """
            DELETE FROM guild_config
            WHERE guild_id = $1
            """,
            guild.id,
        )


def main():
    bot = Bot()
    bot.run(environ.get("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()
