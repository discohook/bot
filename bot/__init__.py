import asyncio
import re
import sys
import traceback
from os import environ

import aiohttp
import asyncpg
import discord
from discord.ext import commands

from bot.utils import wrap_in_code

initial_extensions = (
    "jishaku",
    "bot.ext.meta",
    "bot.ext.help",
    "bot.ext.markdown",
    "bot.ext.utilities",
    "bot.ext.webhooks",
)


error_types = [
    (commands.CommandOnCooldown, "Cooldown"),
    (commands.UserInputError, "Bad input"),
    (commands.CheckFailure, "Check failed"),
]


class Bot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=self._prefix,
            description="Helper bot for Discohook (<https://discohook.org/>)"
            "\nNeed help? Ask in the [support server](https://discohook.org/discord)."
            "\nWant me in your server? [Invite me](https://discohook.org/bot).",
            help_command=None,
            activity=discord.Game(name="at discohook.org | d.help"),
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=False, roles=False
            ),
            max_messages=None,
            guild_subscriptions=False,
        )

        for extension in initial_extensions:
            self.load_extension(extension)

    async def _prefix(self, bot, msg):
        prefix = "d."

        if msg.guild:
            prefix = await self.db.fetchval(
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

    async def start(self, *args, **kwargs):
        self.session = aiohttp.ClientSession()
        self.db = await asyncpg.create_pool(dsn=environ.get("DATABASE_DSN"))
        await super().start(*args, **kwargs)

    async def close(self):
        await self.session.close()
        await self.db.close()
        await super().close()

    async def on_ready(self):
        print(f"Ready as {self.user} ({self.user.id})")

    async def on_message(self, message):
        if message.author.bot:
            return

        if message.guild:
            try:
                has_config = await self.db.fetchval(
                    """
                    SELECT true FROM guild_config
                    WHERE guild_id = $1
                    """,
                    message.guild.id,
                )

                if not has_config:
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
                description = (
                    f"The prefix for Discobot in this server is {wrap_in_code(prefix)}"
                )

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
