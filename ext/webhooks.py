import datetime

import discord
from discord.ext import commands

from .utils import converter


class Webhooks(commands.Cog):
    """Webhook management commands"""

    def _get_webhook_embed(
        self,
        ctx: commands.Context,
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
            else "Use `"
            f"{ctx.prefix}{self.webhook_url.qualified_name} {self.webhook_url.signature}"
            "` to obtain the URL"
        )
        embed.add_field(name="Webhook URL", value=url_message, inline=False)

        return embed

    @commands.group(invoke_without_command=True)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook(self, ctx: commands.Context):
        """Group of commands to manage webhooks in this server"""
        await ctx.send_help("webhook")

    @webhook.command(name="list")
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_list(
        self, ctx: commands.Context, channel: converter.GuildTextChannelConverter = None
    ):
        """Lists webhooks for the server or a given channel"""

        embed = discord.Embed(
            title="Webhooks",
            description=f"Use `{ctx.prefix}{self.webhook_get.qualified_name} {self.webhook_get.signature}`"
            " to get more info on a webhook",
        )

        webhooks = await channel.webhooks() if channel else await ctx.guild.webhooks()
        webhooks = [
            webhook
            for webhook in webhooks
            if webhook.type == discord.WebhookType.incoming
        ]

        for webhook in webhooks[:25]:
            embed.add_field(name=webhook.name, value=f"In {webhook.channel.mention}")

        if len(webhooks) > 25:
            embed.set_footer(
                text=f"Too many webhooks - {len(webhooks) - 25} results omitted"
            )

        await ctx.send(embed=embed)

    @webhook.command(name="get", aliases=["show"], rest_is_raw=True)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_get(
        self, ctx: commands.Context, *, webhook: converter.WebhookConverter,
    ):
        """Shows data for a given webhook"""

        await ctx.send(embed=self._get_webhook_embed(ctx, webhook))

    @webhook.command(name="url", rest_is_raw=True)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_url(
        self, ctx: commands.Context, *, webhook: converter.WebhookConverter,
    ):
        """Obtains the URL for a given webhook"""

        try:
            await ctx.author.send(
                embed=self._get_webhook_embed(ctx, webhook, show_url=True)
            )
        except discord.HTTPException as error:
            if error.code != 403:
                raise

            await ctx.channel.send(
                embed=discord.Embed(
                    title="Forbidden",
                    description="Could not send DM, check server privacy settings or unblock me.",
                )
            )

    @webhook.command(name="new", aliases=["create"], rest_is_raw=True)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_new(
        self,
        ctx: commands.Context,
        channel: converter.GuildTextChannelConverter,
        *,
        name: str,
    ):
        """Creates a new webhook for a given channel"""

        avatar_file = (
            await ctx.message.attachments[0].read()
            if len(ctx.message.attachments) > 0
            else None
        )

        webhook = await channel.create_webhook(name=name, avatar=avatar_file)

        await ctx.send(
            embed=self._get_webhook_embed(ctx, webhook, message="New webhook created")
        )

    @webhook.command(name="edit", aliases=["rename", "avatar"], rest_is_raw=True)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_edit(
        self,
        ctx: commands.Context,
        webhook: converter.WebhookConverter,
        *,
        new_name: str = None,
    ):
        """Edits an existing webhook
        Put the existing webhook name inside quotes
        To edit the avatar, attach a file with the message
        """

        avatar_file = (
            await ctx.message.attachments[0].read()
            if len(ctx.message.attachments) > 0
            else None
        )

        await webhook.edit(name=new_name, avatar=avatar_file)

        webhook = await ctx.bot.fetch_webhook(webhook.id)
        await ctx.send(
            embed=self._get_webhook_embed(ctx, webhook, message="Webhook edited")
        )

    @webhook.command(name="delete", aliases=["remove"], rest_is_raw=True)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_delete(
        self, ctx: commands.Context, *, webhook: converter.WebhookConverter,
    ):
        """Deletes a webhook, this cannot be undone
        Messages sent by this webhook will not be deleted"""

        await webhook.delete()

        await ctx.send(
            embed=discord.Embed(
                title="Webhook deleted",
                description="Messages sent by this webhook have not been deleted",
            )
        )


def setup(bot):
    bot.add_cog(Webhooks(bot))
