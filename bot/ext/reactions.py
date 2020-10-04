import asyncio
import itertools
import re

import discord
from bot.utils import converter, paginators, wrap_in_code
from discord.ext import commands
from discord.utils import get


class Reactions(commands.Cog):
    """Automated actions on message reactions"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, aliases=["rr"])
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole(self, ctx: commands.Context):
        """Group of commands to manage reaction roles"""
        await ctx.send_help("reactionrole")

    @reactionrole.command(name="list")
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_list(self, ctx: commands.Context):
        """Lists all messages with reaction roles enabled"""

        embed = discord.Embed(title="Reaction roles")
        embed.set_footer(
            text="Page {current_page}/{total_pages}, "
            "showing message {first_field}..{last_field}/{total_fields}"
        )
        paginator = paginators.FieldPaginator(ctx.bot, base_embed=embed)

        reaction_roles = itertools.groupby(
            await self.bot.db.fetch(
                """
                SELECT channel_id, message_id, role_id, reaction FROM reaction_role
                WHERE guild_id = $1
                ORDER BY message_id
                """,
                ctx.guild.id,
            ),
            key=lambda rr: (rr["channel_id"], rr["message_id"]),
        )

        for (channel_id, message_id), roles in reaction_roles:
            jump_url = (
                f"https://discord.com/channels/{ctx.guild.id}/{channel_id}/{message_id}"
            )

            paginator.add_field(
                name=f"Message {message_id}",
                value=f"In <#{channel_id}> ([go to message]({jump_url}))\n\n"
                + "\n".join(
                    f"{role['reaction']} \N{RIGHTWARDS ARROW} <@&{role['role_id']}>"
                    for role in roles
                ),
            )

        await paginator.send(target=ctx.channel, owner=ctx.author)

    @reactionrole.command(name="new", aliases=["add", "create"])
    @commands.cooldown(3, 30, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
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
        try:
            await target_message.remove_reaction(event.emoji, ctx.author)
        except discord.Forbidden:
            pass

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
            role_message = await ctx.bot.wait_for(
                "message",
                check=lambda m: m.author.id == ctx.author.id
                and m.channel.id == ctx.channel.id,
                timeout=60.0,
            )
        except asyncio.TimeoutError:
            await prompt_message.edit(
                embed=discord.Embed(
                    title="Cancelled",
                    description="Timeout reached.",
                )
            )
            await target_message.remove_reaction(event.emoji, ctx.me)
            return

        role = None

        if match := re.match(r"([0-9]+)$|<@&([0-9]+)>$", role_message.content):
            role = ctx.guild.get_role(int(match.group(1) or match.group(2)))
        else:
            role = get(ctx.guild.roles, name=role_message.content)

        if role is None:
            await prompt_message.edit(
                embed=discord.Embed(
                    title="Cancelled",
                    description="No role could be found for"
                    f" {wrap_in_code(role_message.content)}.",
                )
            )
            await target_message.remove_reaction(event.emoji, ctx.me)
            return

        if role.managed:
            await prompt_message.edit(
                embed=discord.Embed(
                    title="Cancelled",
                    description="The role is managed by an integration and"
                    " cannot be used.",
                )
            )
            await target_message.remove_reaction(event.emoji, ctx.me)
            return

        if role == ctx.guild.default_role:
            await prompt_message.edit(
                embed=discord.Embed(
                    title="Cancelled",
                    description="You cannot create a reaction role for the"
                    " @everyone role.",
                )
            )
            await target_message.remove_reaction(event.emoji, ctx.me)
            return

        await self.bot.db.execute(
            """
            INSERT INTO reaction_role (message_id, channel_id, guild_id, role_id, reaction)
            VALUES ($1, $2, $3, $4, $5)
            """,
            target_message.id,
            target_message.channel.id,
            ctx.guild.id,
            role.id,
            str(event.emoji),
        )

        check_signature = wrap_in_code(
            f"{ctx.prefix}{self.reactionrole_check.qualified_name}"
        )
        await prompt_message.edit(
            embed=discord.Embed(
                title="Reaction role created",
                description=f"Members that react with {event.emoji} on"
                f" [this message]({target_message.jump_url}) will now be"
                f" assigned the {role.mention} role."
                f"\nMake sure to use {check_signature} to make sure reaction"
                " roles will function correctly in your server.",
            )
        )

    @reactionrole.command(name="delete", aliases=["remove"])
    @commands.cooldown(3, 30, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_delete(self, ctx: commands.Context):
        """Deletes a reaction role for a message"""

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

        await target_message.remove_reaction(event.emoji, ctx.me)

        role_id = await self.bot.db.fetchval(
            """
            DELETE FROM reaction_role
            WHERE message_id = $1 AND reaction = $2
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

    @reactionrole.command(name="check")
    @commands.cooldown(3, 30, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_check(self, ctx: commands.Context):
        """Checks if reaction roles are set up correctly"""

        reaction_roles = await self.bot.db.fetch(
            """
            SELECT channel_id, message_id, role_id FROM reaction_role
            WHERE guild_id = $1
            ORDER BY message_id
            """,
            ctx.guild.id,
        )

        deleted_messages = []
        cannot_read = []
        role_hierachy = []

        for reaction_role in reaction_roles:
            channel = ctx.guild.get_channel(reaction_role["channel_id"])
            if not channel:
                deleted_messages.append(reaction_role)
                continue

            message = None
            try:
                message = await channel.fetch_message(reaction_role["message_id"])
            except discord.NotFound:
                deleted_messages.append(reaction_role)
            except discord.HTTPException:
                cannot_read.append(reaction_role)

            role = ctx.guild.get_role(reaction_role["role_id"])
            if not role:
                deleted_messages.append(reaction_role)
                continue

            if role > ctx.me.top_role:
                role_hierachy.append(reaction_role)

        await self.bot.db.executemany(
            """
            DELETE FROM reaction_role
            WHERE message_id = $1 AND reaction = $2
            """,
            [
                (reaction_role["message_id"], reaction_role["reaction"])
                for role in deleted_messages
            ],
        )

        embed = discord.Embed(
            title="Reaction role automated checkup",
            description="There are problems inside of your server's permission"
            " setup, please fix the issues below to ensure reaction roles will"
            " work inside of your server:",
        )

        if not ctx.me.guild_permissions.manage_roles:
            embed.add_field(
                name="Missing role permissions",
                value="To give members inside of the server the desired"
                " roles, the bot needs to have permission to manage roles.",
                inline=False,
            )

        if len(cannot_read) > 0:
            embed.add_field(
                name="Missing read permissions",
                value="The bot does not have permission to read"
                " message history in the following channels: "
                + ", ".join({f"<#{rr['channel_id']}>" for rr in cannot_read}),
                inline=False,
            )

        if len(role_hierachy) > 0:
            managed_role = get(ctx.me.roles, managed=True) or ctx.me.top_role
            must_win_over = max(ctx.guild.get_role(r["role_id"]) for r in role_hierachy)

            embed.add_field(
                name="Role hierachy issue",
                value="The bot's highest role must be higher than all"
                " reaction roles in the server. To fix this, move the"
                f" {managed_role.mention} role to be above the"
                f" {must_win_over.mention} role.",
                inline=False,
            )

        if len(embed.fields) == 0:
            embed.description = "No issues were found in your server's configuration."

        await ctx.send(embed=embed)

    async def _process_reaction_event(self, event: discord.RawReactionActionEvent):
        role_id = await self.bot.db.fetchval(
            """
            SELECT role_id FROM reaction_role
            WHERE message_id = $1 AND reaction = $2
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
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self.bot.db.execute(
            """
            DELETE FROM reaction_role
            WHERE channel_id = $1
            """,
            channel.id,
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
