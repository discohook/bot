import asyncio
import itertools
import math
import re
from typing import Union

import cachetools
import discord
from bot import cmd, converter, menus
from bot.utils import get_command_signature, wrap_in_code
from discord.ext import commands
from discord.utils import get


class Roles(cmd.Cog):
    """Automated actions on message reactions"""

    def __init__(self, bot):
        super().__init__(bot)

        self.recent_message_cache = cachetools.TTLCache(maxsize=float("inf"), ttl=300)
        self.cache = cachetools.TTLCache(maxsize=float("inf"), ttl=900)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, event: discord.RawReactionActionEvent):
        self.bot.dispatch("raw_reaction_toggle", event)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, event: discord.RawReactionActionEvent):
        self.bot.dispatch("raw_reaction_toggle", event)

    async def prompt_message_emoji(self, ctx: cmd.Context):
        await ctx.prompt(
            embed=discord.Embed(
                title="Creating reaction role",
                description="Select your message by reacting to any message in your "
                "server. Using the emoji that you want the reaction role for.\n\n"
                "Alternatively, if you need a nitro emoji, you can reply with a message "
                "link.",
            )
        )

        done, pending = await asyncio.wait(
            [
                self.bot.wait_for(
                    "raw_reaction_add",
                    check=lambda event: event.user_id == ctx.author.id
                    and event.guild_id == ctx.guild.id,
                    timeout=300.0,
                ),
                self.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == ctx.author.id
                    and m.channel.id == ctx.channel.id,
                ),
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )

        target_message = None
        emoji = None

        result = done.pop().result()

        if isinstance(result, discord.RawReactionActionEvent):
            channel = ctx.guild.get_channel(result.channel_id)
            target_message = await channel.fetch_message(result.message_id)
            emoji = result.emoji

        elif isinstance(result, discord.Message):
            id_re = re.compile(r"^(?:(?P<channel_id>\d+)-)?(?P<message_id>\d+)$")
            link_re = re.compile(
                r"^https?://(?:(?:ptb|canary)\.)?discord(?:app)?\.com/channels/"
                f"{ctx.guild.id}"
                r"/(?P<channel_id>\d+)/(?P<message_id>\d+)/?$"
            )

            match = id_re.match(result.content) or link_re.match(result.content)
            if not match:
                await ctx.prompt(
                    embed=discord.Embed(
                        title="Cancelled",
                        description="No message could be found for"
                        f" {wrap_in_code(result.content)}.",
                    )
                )
                raise commands.BadArgument()

            message_id = int(match.group("message_id"))
            channel_id = int(match.group("channel_id") or 0)

            channel = ctx.guild.get_channel(channel_id)
            if not channel:
                await ctx.prompt(
                    embed=discord.Embed(
                        title="Cancelled",
                        description="No message could be found for"
                        f" {wrap_in_code(result.content)}.",
                    )
                )
                raise commands.BadArgument()

            try:
                target_message = await channel.fetch_message(message_id)
            except discord.HTTPException:
                await ctx.prompt(
                    embed=discord.Embed(
                        title="Cancelled",
                        description="No message could be found for"
                        f" {wrap_in_code(result.content)}.",
                    )
                )
                raise commands.BadArgument()

            await ctx.prompt(
                embed=discord.Embed(
                    title="Creating reaction role",
                    description="Give the name of the server emoji you want the "
                    "reaction role for.\n\nDo not attempt to use the emoji.",
                )
            )

            emoji_message = await self.bot.wait_for(
                "message",
                check=lambda m: m.author.id == ctx.author.id
                and m.channel.id == ctx.channel.id,
                timeout=300.0,
            )

            emoji = get(ctx.guild.emojis, name=emoji_message.content)
            if not emoji or not emoji.is_usable():
                await ctx.prompt(
                    embed=discord.Embed(
                        title="Cancelled",
                        description="No emoji could be found for"
                        f" {wrap_in_code(emoji_message.content)}.",
                    )
                )
                raise commands.BadArgument()

        for future in done:
            future.exception()
        for future in pending:
            future.cancel()

        await target_message.add_reaction(emoji)
        try:
            await target_message.remove_reaction(emoji, ctx.author)
        except discord.HTTPException:
            pass

        return target_message, emoji

    async def prompt_role(self, ctx: cmd.Context):
        await ctx.prompt(
            embed=discord.Embed(
                title="Creating reaction role",
                description="Ping or give the name of the role that should be "
                "granted when a user reacts to this message.",
            )
        )

        role_message = await self.bot.wait_for(
            "message",
            check=lambda m: m.author.id == ctx.author.id
            and m.channel.id == ctx.channel.id,
            timeout=300.0,
        )

        role = None

        if match := re.match(r"(\d+)$|<@&(\d+)>$", role_message.content):
            role = ctx.guild.get_role(int(match.group(1) or match.group(2)))
        else:
            role = get(ctx.guild.roles, name=role_message.content)

        if not role:
            await ctx.prompt(
                embed=discord.Embed(
                    title="Cancelled",
                    description="No role could be found for"
                    f" {wrap_in_code(role_message.content)}.",
                )
            )
            raise commands.BadArgument()

        return role

    @commands.group(invoke_without_command=True, aliases=["rr"])
    @commands.cooldown(4, 4, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole(self, ctx: cmd.Context):
        """Group of commands to manage reaction roles"""
        await ctx.send_help("reactionrole")

    @reactionrole.command(name="list")
    @commands.cooldown(4, 4, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_list(self, ctx: cmd.Context):
        """Lists all messages with reaction roles enabled"""

        embed = discord.Embed(title="Reaction roles")
        embed.set_footer(
            text="Page {current_page}/{total_pages}, "
            "showing message {first_field}..{last_field}/{total_fields}"
        )
        paginator = menus.FieldPaginator(self.bot, base_embed=embed)

        reaction_roles = itertools.groupby(
            await self.db.fetch(
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

        await paginator.send(ctx)

    @reactionrole.command(name="new", aliases=["add", "create"])
    @commands.cooldown(3, 8, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_new(self, ctx: cmd.Context):
        """Creates a new reaction role"""

        count = await self.db.fetchval(
            """
            SELECT COUNT(*) FROM reaction_role
            WHERE guild_id = $1
            """,
            ctx.guild.id,
        )
        if count >= 250:
            await ctx.prompt(
                embed=discord.Embed(
                    title="Limit reached",
                    description="You have reached the maximum number of"
                    " reaction roles in this server. Please clean up any"
                    " reaction roles that you no longer need.",
                )
            )
            return

        target_message = None
        emoji = None
        role = None

        try:
            target_message, emoji = await self.prompt_message_emoji(ctx)

            role_id = await self.db.fetchval(
                """
                SELECT role_id FROM reaction_role
                WHERE message_id = $1 AND reaction = $2
                """,
                target_message.id,
                str(emoji),
            )
            if role_id:
                role = ctx.guild.get_role(role_id)
                if role:
                    await ctx.prompt(
                        embed=discord.Embed(
                            title="Already exists",
                            description=f"Reaction role for {emoji} on"
                            f" [this message]({target_message.jump_url}) already"
                            " exists.",
                        )
                    )
                    return

                await self.db.execute(
                    """
                    DELETE FROM reaction_role
                    WHERE message_id = $1 AND reaction = $2
                    """,
                    target_message.id,
                    str(emoji),
                )

            role = await self.prompt_role(ctx)
        except asyncio.TimeoutError:
            await ctx.prompt(
                embed=discord.Embed(
                    title="Cancelled",
                    description="Timeout reached.",
                )
            )

            if target_message and emoji:
                try:
                    await target_message.remove_reaction(emoji, ctx.me)
                except discord.NotFound:
                    pass
            return
        except commands.BadArgument:
            if target_message and emoji:
                try:
                    await target_message.remove_reaction(emoji, ctx.me)
                except discord.NotFound:
                    pass
            return

        if role.managed:
            await ctx.prompt(
                embed=discord.Embed(
                    title="Cancelled",
                    description="The role is managed by an integration and"
                    " cannot be used.",
                )
            )
            try:
                await target_message.remove_reaction(emoji, ctx.me)
            except discord.NotFound:
                pass
            return

        if role == ctx.guild.default_role:
            await ctx.prompt(
                embed=discord.Embed(
                    title="Cancelled",
                    description="You cannot create a reaction role for the"
                    " @everyone role.",
                )
            )
            try:
                await target_message.remove_reaction(emoji, ctx.me)
            except discord.NotFound:
                pass
            return

        await self.db.execute(
            """
            INSERT INTO reaction_role (message_id, channel_id, guild_id, role_id, reaction)
            VALUES ($1, $2, $3, $4, $5)
            """,
            target_message.id,
            target_message.channel.id,
            ctx.guild.id,
            role.id,
            str(emoji),
        )

        self.cache.pop((target_message.id, str(emoji)), None)
        self.recent_message_cache.pop(target_message.id, None)

        await ctx.prompt(
            embed=discord.Embed(
                title="Reaction role created",
                description=f"Members that react with {emoji} on"
                f" [this message]({target_message.jump_url}) will now be"
                f" assigned the {role.mention} role."
                f"\nMake sure to use {get_command_signature(ctx, self.reactionrole_check)}"
                " to make sure reaction roles will function correctly in your server.",
            )
        )

    @reactionrole.command(name="delete", aliases=["remove"])
    @commands.cooldown(3, 8, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_delete(self, ctx: cmd.Context):
        """Deletes a reaction role for a message"""

        prompt_message = await ctx.prompt(
            embed=discord.Embed(
                title="Deleting reaction role",
                description="Toggle any reaction that is managed by this bot "
                "to remove the integration.",
            )
        )

        event = None
        try:
            event = await self.bot.wait_for(
                "raw_reaction_toggle",
                check=lambda event: event.user_id == ctx.author.id
                and event.guild_id == ctx.guild.id,
                timeout=300.0,
            )
        except asyncio.TimeoutError:
            await ctx.prompt(
                embed=discord.Embed(
                    title="Cancelled",
                    description="Timeout reached.",
                )
            )
            return

        channel = ctx.guild.get_channel(event.channel_id)
        target_message = await channel.fetch_message(event.message_id)

        try:
            await target_message.remove_reaction(event.emoji, ctx.me)
        except discord.NotFound:
            pass

        role_id = await self.db.fetchval(
            """
            DELETE FROM reaction_role
            WHERE message_id = $1 AND reaction = $2
            RETURNING role_id
            """,
            target_message.id,
            str(event.emoji),
        )

        self.cache.pop((target_message.id, str(event.emoji)), None)

        if not role_id:
            await ctx.prompt(
                embed=discord.Embed(
                    title="Not found",
                    description="There was no reaction role configured for the"
                    f" {event.emoji} reactions on [this message]({target_message.jump_url}).",
                )
            )
            return

        await ctx.prompt(
            embed=discord.Embed(
                title="Deleted reaction role",
                description=f"Members that react with {event.emoji} on"
                f" [this message]({target_message.jump_url}) will no longer be"
                f" assigned the <@&{role_id}> role.",
            )
        )

    @reactionrole.group(invoke_without_command=True, name="clear")
    @commands.cooldown(3, 8, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_clear(self, ctx: cmd.Context):
        """Sub group of commands to clear reaction roles in the server"""
        await ctx.send_help("reactionrole clear")

    @reactionrole_clear.command(name="all")
    @commands.cooldown(3, 8, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_clear_all(self, ctx: cmd.Context):
        """Clears all reaction roles in this server"""

        reaction_roles = await self.db.fetch(
            """
            DELETE FROM reaction_role
            WHERE guild_id = $1
            RETURNING message_id, reaction
            """,
            ctx.guild.id,
        )

        if len(reaction_roles) <= 0:
            await ctx.prompt(
                embed=discord.Embed(
                    title="Couldn't clear reaction roles",
                    description=f"No reaction roles were configured for this server.",
                )
            )
            return

        messages = {rr["message_id"] for rr in reaction_roles}

        await ctx.prompt(
            embed=discord.Embed(
                title="Cleared reaction roles",
                description=f"Successfully cleared {len(reaction_roles)} reaction "
                f"roles from {len(messages)} messages.",
            )
        )

    @reactionrole_clear.command(name="message")
    @commands.cooldown(4, 4, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_clear_message(
        self, ctx: cmd.Context, *, message: Union[converter.MessageConverter, int]
    ):
        """Clears reaction roles for a given message"""

        reaction_roles = await self.db.fetch(
            """
            DELETE FROM reaction_role
            WHERE message_id = $1
            RETURNING reaction
            """,
            message.id if isinstance(message, discord.Message) else message,
        )

        if len(reaction_roles) <= 0:
            await ctx.prompt(
                embed=discord.Embed(
                    title="Couldn't clear reaction roles",
                    description=f"No reaction roles were configured for this message.",
                )
            )
            return

        await ctx.prompt(
            embed=discord.Embed(
                title="Cleared reaction roles",
                description=f"Successfully cleared {len(reaction_roles)} reaction "
                "roles.",
            )
        )

    @reactionrole_clear.command(name="role")
    @commands.cooldown(3, 8, commands.BucketType.member)
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_clear_role(self, ctx: cmd.Context, *, role: discord.Role):
        """Clears reaction roles for a given role"""

        reaction_roles = await self.db.fetch(
            """
            DELETE FROM reaction_role
            WHERE role_id = $1
            RETURNING message_id, reaction
            """,
            role.id if isinstance(role, discord.Role) else role,
        )

        if len(reaction_roles) <= 0:
            await ctx.prompt(
                embed=discord.Embed(
                    title="Couldn't clear reaction roles",
                    description=f"No reaction roles were configured for this role.",
                )
            )
            return

        messages = {rr["message_id"] for rr in reaction_roles}

        await ctx.prompt(
            embed=discord.Embed(
                title="Cleared reaction roles",
                description=f"Successfully cleared {len(reaction_roles)} reaction "
                f"roles from {len(messages)} messages.",
            )
        )

    @reactionrole.command(name="check")
    @commands.cooldown(3, 30, commands.BucketType.member)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_roles=True)
    async def reactionrole_check(self, ctx: cmd.Context):
        """Checks if reaction roles are set up correctly"""

        async with ctx.typing():
            reaction_roles = await self.db.fetch(
                """
                SELECT channel_id, message_id, role_id, reaction FROM reaction_role
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

            await self.db.executemany(
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
                must_win_over = max(
                    ctx.guild.get_role(r["role_id"]) for r in role_hierachy
                )

                embed.add_field(
                    name="Role hierachy issue",
                    value="The bot's highest role must be higher than all"
                    " reaction roles in the server. To fix this, move the"
                    f" {managed_role.mention} role to be above the"
                    f" {must_win_over.mention} role.",
                    inline=False,
                )

            if len(embed.fields) == 0:
                embed.description = (
                    "No issues were found in your server's configuration."
                )

            await ctx.prompt(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        self.recent_message_cache[message.id] = True

    @commands.Cog.listener()
    async def on_raw_reaction_toggle(self, event: discord.RawReactionActionEvent):
        if event.message_id in self.recent_message_cache:
            return

        role_id = None
        try:
            role_id = self.cache[(event.message_id, str(event.emoji))]
        except KeyError:
            role_id = await self.db.fetchval(
                """
                SELECT role_id FROM reaction_role
                WHERE message_id = $1 AND reaction = $2
                """,
                event.message_id,
                str(event.emoji),
            )
            self.cache[(event.message_id, str(event.emoji))] = role_id

        if not role_id:
            return

        member = None
        try:
            guild = self.bot.get_guild(event.guild_id)
            member = await guild.fetch_member(event.user_id)
        except discord.NotFound:
            return

        try:
            if event.event_type == "REACTION_ADD":
                await member.add_roles(discord.Object(id=role_id))
            elif event.event_type == "REACTION_REMOVE":
                await member.remove_roles(discord.Object(id=role_id))
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_raw_message_delete(self, event: discord.RawMessageDeleteEvent):
        await self.db.execute(
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
        await self.db.execute(
            """
            DELETE FROM reaction_role
            WHERE message_id = any($1::bigint[])
            """,
            event.message_ids,
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self.db.execute(
            """
            DELETE FROM reaction_role
            WHERE channel_id = $1
            """,
            channel.id,
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        await self.db.execute(
            """
            DELETE FROM reaction_role
            WHERE role_id = $1
            """,
            role.id,
        )


def setup(bot):
    bot.add_cog(Roles(bot))
