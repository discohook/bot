import re
from os import environ

import aiohttp
import asyncpg
import discord
from discord.ext import commands
from discord.utils import get

import bot.patches
from bot import cmd
from bot.ext import config
from bot.utils import wrap_in_code

initial_extensions = (
    "jishaku",
    "bot.ext.config",
    "bot.ext.meta",
    "bot.ext.help",
    "bot.ext.errors",
    "bot.ext.markdown",
    "bot.ext.utilities",
    "bot.ext.webhooks",
    "bot.ext.roles",
)


class Bot(commands.AutoShardedBot):
    def __init__(self):
        shard_kwargs = {}
        if "CLUSTER_ID" in environ:
            cluster_id = int(environ.get("CLUSTER_ID"))
            total_clusters = int(environ.get("CLUSTER_COUNT"))
            total_shards = int(environ.get("SHARD_COUNT"))

            shard_kwargs["shard_ids"] = list(
                range(cluster_id, total_shards, total_clusters)
            )
            shard_kwargs["shard_count"] = total_shards

        super().__init__(
            command_prefix=self.get_prefix_list,
            description="Discohook's official bot.",
            help_command=None,
            activity=discord.Game(name="discohook.app | d.help"),
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                roles=False,
                users=False,
                replied_user=True,
            ),
            intents=discord.Intents(
                guilds=True,
                messages=True,
                emojis=True,
                reactions=True,
            ),
            member_cache_flags=discord.MemberCacheFlags.none(),
            max_messages=None,
            guild_subscriptions=False,
            **shard_kwargs,
        )

        self.add_check(self.global_check)

        for extension in initial_extensions:
            self.load_extension(extension)

    async def start(self, *args, **kwargs):
        self.session = aiohttp.ClientSession()
        self.pool = await asyncpg.create_pool(dsn=environ.get("DATABASE_DSN"))
        await super().start(*args, **kwargs)

    async def close(self):
        await self.session.close()
        await self.pool.close()
        await super().close()

    async def get_prefix_list(self, bot, message):
        cfg = self.get_cog("Config")

        prefix = (
            await cfg.get_value(message.guild, get(config.configurables, name="prefix"))
            if message.guild
            else "d."
        )

        return (
            f"<@!{bot.user.id}> ",
            f"<@{bot.user.id}> ",
            f"{prefix} ",
            prefix,
        )

    async def global_check(self, ctx):
        await commands.bot_has_permissions(
            send_messages=True,
            embed_links=True,
            attach_files=True,
        ).predicate(ctx)

        return True

    async def on_ready(self):
        print(f"Ready as {self.user} ({self.user.id})")

    async def on_message(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message, cls=cmd.Context)
        cfg = self.get_cog("Config")

        if re.fullmatch(rf"<@!?{self.user.id}>", message.content):
            embed = discord.Embed(title="Prefix", description="My prefix is `d.`.")

            if message.guild:
                try:
                    await self.global_check(ctx)
                except commands.BotMissingPermissions as error:
                    await self.get_cog("Errors").on_command_error(ctx, error)
                    return

                prefix = await cfg.get_value(
                    message.guild, get(config.configurables, name="prefix")
                )
                embed.description = f"My prefix is {wrap_in_code(prefix)}."

            await message.channel.send(embed=embed)

        await self.invoke(ctx)

    async def on_error(self, event, *args, **kwargs):
        errors = self.get_cog("Errors")
        if errors:
            await errors.on_error(event, *args, **kwargs)
