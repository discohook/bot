import discord
from bot.ext import config
from discord.ext import commands
from discord.utils import get


def sensitive():
    check_guild = commands.guild_only().predicate
    has_bypass = commands.has_guild_permissions(manage_messages=True).predicate

    async def extended_check(ctx):
        await check_guild(ctx)

        sensitive = await ctx.bot.get_cog("Config").get_value(
            ctx.guild, get(config.configurables, name="private")
        )

        if sensitive:
            return await has_bypass(ctx)

        return True

    return commands.check(extended_check)
