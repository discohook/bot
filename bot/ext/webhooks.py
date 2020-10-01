import asyncio
import datetime

import discord
from bot.utils import converter, wrap_in_code
from discord.ext import commands
from jishaku import metacog


class Webhooks(commands.Cog):
    """Webhook management"""

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

        url_signature = wrap_in_code(
            f"{ctx.prefix}{self.webhook_url.qualified_name} {self.webhook_url.signature}"
        )
        url_message = (
            webhook.url if show_url else f"Use {url_signature} to obtain the URL"
        )
        embed.add_field(name="Webhook URL", value=url_message, inline=False)

        return embed

    @commands.group(invoke_without_command=True)
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook(self, ctx: commands.Context):
        """Group of commands to manage webhooks"""
        await ctx.send_help("webhook")

    @webhook.command(name="list")
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_list(
        self,
        ctx: commands.Context,
        channel: converter.GuildTextChannelConverter = None,
    ):
        """Lists webhooks for the server or a given channel"""

        get_signature = wrap_in_code(
            f"{ctx.prefix}{self.webhook_get.qualified_name} {self.webhook_get.signature}"
        )
        embed = discord.Embed(
            title="Webhooks",
            description=f"Use {get_signature} to get more info on a webhook",
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
                text=f"Too many webhooks - {len(webhooks) - 25} results omitted."
            )

        await ctx.send(embed=embed)

    @webhook.command(name="get", aliases=["show"])
    @commands.cooldown(3, 8, commands.BucketType.member)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_get(
        self,
        ctx: commands.Context,
        *,
        webhook: converter.WebhookConverter,
    ):
        """Shows data for a given webhook"""

        await ctx.send(embed=self._get_webhook_embed(ctx, webhook))

    @webhook.command(name="url")
    @commands.cooldown(3, 8, commands.BucketType.member)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_url(
        self,
        ctx: commands.Context,
        *,
        webhook: converter.WebhookConverter,
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

    @webhook.command(name="new", aliases=["add", "create"])
    @commands.cooldown(3, 30, commands.BucketType.member)
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

    @webhook.command(name="edit", aliases=["rename", "avatar"])
    @commands.cooldown(3, 30, commands.BucketType.member)
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
        The existing webhook name must be put in quotes, but not the new name (if any)
        To edit the avatar, attach a image file with the message
        """

        avatar_file = (
            await ctx.message.attachments[0].read()
            if len(ctx.message.attachments) > 0
            else None
        )

        if avatar_file is None and new_name is None:
            raise commands.UserInputError("No new name or avatar was given")

        await webhook.edit(name=new_name, avatar=avatar_file)

        webhook = await ctx.bot.fetch_webhook(webhook.id)
        await ctx.send(
            embed=self._get_webhook_embed(ctx, webhook, message="Webhook edited")
        )

    @webhook.command(name="delete", aliases=["remove"])
    @commands.cooldown(3, 30, commands.BucketType.member)
    @commands.has_guild_permissions(manage_webhooks=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook_delete(
        self,
        ctx: commands.Context,
        *,
        webhook: converter.WebhookConverter,
    ):
        """Deletes a webhook, this cannot be undone
        Messages sent by this webhook will not be deleted"""

        message = await ctx.send(
            embed=discord.Embed(
                title="Confirmation",
                description=f"Are you sure you want to delete {wrap_in_code(webhook.name)}? This action cannot be reverted.",
            )
        )

        await message.add_reaction("\N{WASTEBASKET}")

        try:
            await ctx.bot.wait_for(
                "raw_reaction_add",
                timeout=30.0,
                check=lambda event: (
                    str(event.emoji) == "\N{WASTEBASKET}"
                    and event.message_id == message.id
                    and event.user_id == ctx.author.id
                ),
            )
        except asyncio.TimeoutError:
            await message.edit(
                embed=discord.Embed(
                    title="Confirmation cancelled",
                    description="30 second timeout reached",
                )
            )
        else:
            await webhook.delete()

            await message.edit(
                embed=discord.Embed(
                    title="Webhook deleted",
                    description="Messages sent by this webhook have not been deleted",
                )
            )
        finally:
            await message.remove_reaction("\N{WASTEBASKET}", ctx.guild.me)


def setup(bot):
    bot.add_cog(Webhooks(bot))
