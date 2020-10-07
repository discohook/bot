import asyncio
import collections
import pprint
from os import environ

import asyncpg
import discord
from bot.utils import cog, paginators, wrap_in_code
from discord.ext import commands
from discord.utils import get

Configurable = collections.namedtuple(
    "Configurable",
    "name description column type",
)


configurables = [
    Configurable(
        name="prefix",
        description="Prefix specific to server, mention prefix will always work.",
        column="prefix",
        type=str,
    ),
    Configurable(
        name="private",
        description="Make certain sensitive commands private to server moderators.",
        column="commands_private",
        type=bool,
    ),
]


type_names = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


def resolve_value(expected_type, user_input: str):
    if expected_type is bool:
        lowered = user_input.lower()
        if lowered in ("yes", "y", "true", "t", "1", "enable", "on"):
            return True
        elif lowered in ("no", "n", "false", "f", "0", "disable", "off"):
            return False
        else:
            raise RuntimeError(f"{user_input!r} can't be resolved to {expected_type}")

    try:
        return expected_type(user_input)
    except:
        raise RuntimeError(f"{user_input!r} can't be resolved to {expected_type}")


class Config(cog.Cog):
    """State management for the bot"""

    def __init__(self, bot):
        super().__init__(bot)

        self.cache = {}

        self.ready = asyncio.Event()
        if self.loop.is_running():
            self.loop.create_task(self.init())
        else:
            self.loop.run_until_complete(self.init())
        self.ready.set()

    async def init(self):
        self.pool = await asyncpg.create_pool(dsn=environ.get("DATABASE_DSN"))

    async def ensure(self, guild: discord.Guild):
        await self.ready.wait()

        if guild.id in self.cache:
            return self.cache[guild.id]

        row = await self.db.fetchrow(
            """
            SELECT * FROM guild_config
            WHERE guild_id = $1
            """,
            guild.id,
        )
        if row:
            self.cache[guild.id] = dict(row)
            return await self.ensure(guild)

        await self.db.execute(
            """
            INSERT INTO guild_config (guild_id)
            VALUES ($1)
            ON CONFLICT DO NOTHING
            """,
            guild.id,
        )

        return await self.ensure(guild)

    async def get_value(
        self,
        guild: discord.Guild,
        configurable: Configurable,
    ):
        config = await self.ensure(guild)
        return config[configurable.column]

    async def set_value(
        self,
        guild: discord.Guild,
        configurable: Configurable,
        new_value,
    ):
        config = await self.ensure(guild)

        config[configurable.column] = new_value

        await self.db.execute(
            f"""
            UPDATE guild_config
            SET {configurable.column} = $2
            WHERE guild_id = $1
            """,
            guild.id,
            new_value,
        )


def setup(bot: commands.Bot):
    config = Config(bot)
    bot.add_cog(config)
