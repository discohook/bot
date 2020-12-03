import asyncio

import discord
from bot import cmd, converter, menus
from bot.utils import get_command_signature, wrap_in_code
from discord.ext import commands


class Webhooks(cmd.Cog):
    """Webhook management"""

    def get_webhook_embed(
        self,
        ctx: cmd.Context,
        webhook: discord.Webhook,
        *,
        message=None,
        show_url=False,
    ):
        embed = discord.Embed(
            title=f"{message}: {webhook.name}" if message else webhook.name
        )
        embed.set_thumbnail(url=str(webhook.avatar_url))

        embed.add_field(name="Channel", value=webhook.channel.mention)
        embed.add_field(
            name="Created at",
            value=f"{webhook.created_at.ctime()} UTC".replace("  ", " "),
        )

        url_message = (
            webhook.url
            if show_url
            else f"Use {get_command_signature(ctx, self.webhook_url)} to obtain the URL."
        )
        embed.add_field(name="Webhook URL", value=url_message, inline=False)

        return embed

    @commands.group(invoke_without_command=True)
    @commands.cooldown(4, 4, commands.BucketType.member)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook(self, ctx: cmd.Context):
        """Group of commands to manage webhooks"""
        await ctx.send_help("webhook")

    @webhook.command(name="list")
    @commands.cooldown(4, 4, commands.BucketType.member)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_list(self, ctx: cmd.Context, channel: discord.TextChannel = None):
        """Lists webhooks for the server or a given channel"""

        embed = discord.Embed(
            title="Webhooks",
            description=f"Use {get_command_signature(ctx, self.webhook_get)}"
            " to get more info on a webhook.",
        )
        embed.set_footer(
            text="Page {current_page}/{total_pages}, "
            "showing webhook {first_field}..{last_field}/{total_fields}."
        )
        paginator = menus.FieldPaginator(self.bot, base_embed=embed)

        for webhook in await ctx.guild.webhooks():
            if webhook.type != discord.WebhookType.incoming:
                continue
            if channel and webhook.channel_id != channel.id:
                continue

            paginator.add_field(
                name=webhook.name,
                value=f"In {webhook.channel.mention}",
            )

        await paginator.send(target=ctx.channel, owner=ctx.author)

    @webhook.command(name="get", aliases=["show"])
    @commands.cooldown(3, 8, commands.BucketType.member)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_get(
        self, ctx: cmd.Context, *, webhook: converter.WebhookConverter
    ):
        """Shows data for a given webhook"""

        await ctx.send(embed=self.get_webhook_embed(ctx, webhook))

    @webhook.command(name="url")
    @commands.cooldown(3, 8, commands.BucketType.member)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_url(
        self, ctx: cmd.Context, *, webhook: converter.WebhookConverter
    ):
        """Obtains the URL for a given webhook"""

        try:
            await ctx.author.send(
                embed=self.get_webhook_embed(ctx, webhook, show_url=True)
            )
            await ctx.channel.send(
                embed=discord.Embed(
                    title="Webhook URL sent",
                    description="Because the URL should be kept secret, a message has been sent to your DMs.",
                )
            )
        except discord.Forbidden:
            await ctx.channel.send(
                embed=discord.Embed(
                    title="Forbidden",
                    description="Could not send DM, check server privacy settings or unblock me.",
                )
            )

    @webhook.command(name="new", aliases=["add", "create"])
    @commands.cooldown(3, 30, commands.BucketType.member)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_new(
        self, ctx: cmd.Context, channel: discord.TextChannel, *, name: str
    ):
        """Creates a new webhook for a given channel"""

        avatar_file = (
            await ctx.message.attachments[0].read()
            if len(ctx.message.attachments) > 0
            else None
        )

        webhook = await channel.create_webhook(name=name, avatar=avatar_file)

        await ctx.send(
            embed=self.get_webhook_embed(ctx, webhook, message="New webhook created")
        )

    @webhook.command(name="edit", aliases=["rename", "avatar"])
    @commands.cooldown(3, 30, commands.BucketType.member)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_edit(
        self,
        ctx: cmd.Context,
        webhook: converter.WebhookConverter,
        *,
        new_name: str = None,
    ):
        """Edits an existing webhook
        The existing webhook name must be put in quotes, but not the new name (if any)
        To edit the avatar, attach a image file with the message
        """

        edit_kwargs = {}

        if new_name:
            edit_kwargs["name"] = new_name

        if len(ctx.message.attachments) > 0:
            edit_kwargs["avatar"] = await ctx.message.attachments[0].read()

        if len(edit_kwargs.keys()) <= 0:
            raise commands.UserInputError("No new name or avatar was given")

        await webhook.edit(**edit_kwargs)

        webhook = await self.bot.fetch_webhook(webhook.id)
        await ctx.send(
            embed=self.get_webhook_embed(ctx, webhook, message="Webhook edited")
        )

    @webhook.command(name="delete", aliases=["remove"])
    @commands.cooldown(3, 30, commands.BucketType.member)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_delete(
        self, ctx: cmd.Context, *, webhook: converter.WebhookConverter
    ):
        """Deletes a webhook, this cannot be undone
        Messages sent by this webhook will not be deleted"""

        message = await ctx.send(
            embed=discord.Embed(
                title="Confirmation",
                description=f"Are you sure you want to delete {wrap_in_code(webhook.name)}?"
                " This action cannot be reverted.",
            )
        )

        await message.add_reaction("\N{WASTEBASKET}")

        try:
            await self.bot.wait_for(
                "raw_reaction_add",
                timeout=30.0,
                check=lambda event: (
                    str(event.emoji) == "\N{WASTEBASKET}"
                    and event.message_id == message.id
                    and event.user_id == ctx.author.id
                ),
            )
        except asyncio.TimeoutError:
            await ctx.send(
                embed=discord.Embed(
                    title="Confirmation cancelled",
                    description="30 second timeout reached",
                )
            )
        else:
            await webhook.delete()

            await ctx.send(
                embed=discord.Embed(
                    title="Webhook deleted",
                    description="Messages sent by this webhook have not been deleted.",
                )
            )
        finally:
            await message.remove_reaction("\N{WASTEBASKET}", ctx.guild.me)


def setup(bot):
    bot.add_cog(Webhooks(bot))
