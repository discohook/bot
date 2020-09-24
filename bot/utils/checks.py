import discord
from discord.ext import commands


def private_command():
    check_guild = commands.guild_only().predicate
    has_bypass = commands.has_guild_permissions(manage_messages=True).predicate

    async def extended_check(ctx):
        await check_guild(ctx)

        commands_private = await ctx.bot.db.fetchval(
            """
            SELECT commands_private FROM guild_config
            WHERE guild_id = $1
            """,
            ctx.guild.id,
        )

        if commands_private:
            return await has_bypass(ctx)

        return True

    return commands.check(extended_check)
