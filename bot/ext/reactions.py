import asyncio

import discord
from bot.utils import converter
from discord.ext import commands
from discord.utils import get


class Reactions(commands.Cog):
    """Automated actions on message reactions"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, aliases=["rr"])
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(
        read_message_history=True, manage_roles=True, manage_messages=True
    )
    async def reactionrole(self, ctx: commands.Context):
        """Group of commands to manage reaction roles"""
        await ctx.send_help("reactionrole")

    @reactionrole.command(name="new", aliases=["add", "create"])
    @commands.cooldown(3, 30, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(
        read_message_history=True, manage_roles=True, manage_messages=True
    )
    async def reactionrole_new(self, ctx: commands.Context):
        """Creates a new reaction role"""

        prompt_message = await ctx.send(
            embed=discord.Embed(
                title="Creating reaction role",
                description="Give any message in your server a reaction to"
                " create a reaction role. You have 60 seconds to do this.",
            )
        )

        event = None
        try:
            event = await ctx.bot.wait_for(
                "raw_reaction_add",
                check=lambda event: event.user_id == ctx.author.id
                and event.guild_id == ctx.guild.id,
                timeout=60.0,
            )
        except asyncio.TimeoutError:
            await prompt_message.edit(
                embed=discord.Embed(
                    title="Cancelled",
                    description="Timeout reached.",
                )
            )
            return

        channel = ctx.guild.get_channel(event.channel_id)
        target_message = await channel.fetch_message(event.message_id)

        await target_message.add_reaction(event.emoji)
        await target_message.remove_reaction(event.emoji, ctx.author)

        await prompt_message.edit(
            embed=discord.Embed(
                title="Creating reaction role",
                description="Ping or give the name of the role that should be"
                " granted when a user reacts to this message."
                " You have 60 seconds to do this.",
            )
        )

        role_message = None
        try:
            role_message = await ctx.bot.wait_for("message", timeout=60.0)
        except asyncio.TimeoutError:
            await prompt_message.edit(
                embed=discord.Embed(
                    title="Cancelled",
                    description="Timeout reached.",
                )
            )
            return

        role = await converter.GuildRoleConverter().convert(ctx, role_message.content)

        await self.bot.db.execute(
            """
            INSERT INTO reaction_role (message_id, guild_id, role_id, emoji)
            VALUES ($1, $2, $3, $4)
            """,
            target_message.id,
            ctx.guild.id,
            role.id,
            str(event.emoji),
        )

        await prompt_message.edit(
            embed=discord.Embed(
                title="Reaction role created",
                description=f"Members that react with {event.emoji} on"
                f" [this message]({target_message.jump_url}) will now be"
                f" assigned the {role.mention} role.",
            )
        )

    @reactionrole.command(name="delete", aliases=["remove"])
    @commands.cooldown(3, 30, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(
        read_message_history=True, manage_roles=True, manage_messages=True
    )
    async def reactionrole_delete(self, ctx: commands.Context):
        prompt_message = await ctx.send(
            embed=discord.Embed(
                title="Deleting reaction role",
                description="Toggle any reaction that is managed by this bot"
                " to remove the integration. You have 60 seconds to do this.",
            )
        )

        event = None
        done, pending = await asyncio.wait(
            [
                ctx.bot.wait_for(
                    "raw_reaction_add",
                    check=lambda event: event.user_id == ctx.author.id
                    and event.guild_id == ctx.guild.id,
                    timeout=60.0,
                ),
                ctx.bot.wait_for(
                    "raw_reaction_remove",
                    check=lambda event: event.user_id == ctx.author.id
                    and event.guild_id == ctx.guild.id,
                ),
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )

        try:
            event = done.pop().result()
        except asyncio.TimeoutError:
            await prompt_message.edit(
                embed=discord.Embed(
                    title="Cancelled",
                    description="Timeout reached.",
                )
            )
            return
        for future in done:
            future.exception()
        for future in pending:
            future.cancel()

        channel = ctx.guild.get_channel(event.channel_id)
        target_message = await channel.fetch_message(event.message_id)

        role_id = await self.bot.db.fetchval(
            """
            DELETE FROM reaction_role
            WHERE message_id = $1 AND emoji = $2
            RETURNING role_id
            """,
            target_message.id,
            str(event.emoji),
        )

        role = get(ctx.guild.roles, id=role_id)

        await prompt_message.edit(
            embed=discord.Embed(
                title="Deleted reaction role",
                description=f"Members that react with {event.emoji} on"
                f" [this message]({target_message.jump_url}) will no longer be"
                f" assigned the {role.mention} role.",
            )
        )

    async def _process_reaction_event(self, event: discord.RawReactionActionEvent):
        role_id = await self.bot.db.fetchval(
            """
            SELECT role_id FROM reaction_role
            WHERE message_id = $1 AND emoji = $2
            """,
            event.message_id,
            str(event.emoji),
        )

        if not role_id:
            return

        member = await self.bot.get_guild(event.guild_id).fetch_member(event.user_id)

        if not member:
            return

        if event.event_type == "REACTION_ADD":
            await member.add_roles(discord.Object(id=role_id))
        elif event.event_type == "REACTION_REMOVE":
            await member.remove_roles(discord.Object(id=role_id))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, event: discord.RawReactionActionEvent):
        await self._process_reaction_event(event)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, event: discord.RawReactionActionEvent):
        await self._process_reaction_event(event)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, event: discord.RawMessageDeleteEvent):
        await self.bot.db.execute(
            """
            DELETE FROM reaction_role
            WHERE message_id = $1
            """,
            event.message_id,
        )

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(
        self, event: discord.RawBulkMessageDeleteEvent
    ):
        await self.bot.db.execute(
            """
            DELETE FROM reaction_role
            WHERE message_id = any($1::bigint[])
            """,
            event.message_ids,
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        await self.bot.db.execute(
            """
            DELETE FROM reaction_role
            WHERE role_id = $1
            """,
            role.id,
        )


def setup(bot):
    bot.add_cog(Reactions(bot))
