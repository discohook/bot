import asyncio
import io
import json
import typing

import discord
from bot.ext import config
from bot.utils import cog, paginators, wrap_in_code
from discord.ext import commands
from discord.utils import get


class Meta(cog.Cog):
    """Commands related to the bot itself"""

    @commands.group(invoke_without_command=True)
    @commands.cooldown(3, 8, commands.BucketType.channel)
    @commands.guild_only()
    async def config(
        self,
        ctx: commands.Context,
        option: typing.Optional[str],
        *,
        new_value: typing.Optional[str],
    ):
        """Manages server configuration for bot"""

        command = f"{ctx.prefix}{self.config.qualified_name}"

        if option:
            configurable = get(config.configurables, name=option.lower())
            if configurable is None:
                raise commands.UserInputError(
                    f"Option {wrap_in_code(option)} not found"
                )

            if new_value:
                await commands.has_guild_permissions(manage_guild=True).predicate(ctx)

                try:
                    parsed_value = config.resolve_value(configurable.type, new_value)
                    await self.cfg.set_value(ctx.guild, configurable, parsed_value)
                except:
                    raise commands.BadArgument(
                        f"Value {wrap_in_code(new_value)} is does not fit"
                        f" expected type {config.type_names[configurable.type]}"
                    )

            value = (
                parsed_value
                if new_value is not None
                else await self.cfg.get_value(ctx.guild, configurable)
            )
            value = (
                ("yes" if value else "no") if isinstance(value, bool) else str(value)
            )
            value = wrap_in_code(value)

            set_configurable_signature = wrap_in_code(
                f"{command} {configurable.name} <new value>"
            )
            message = (
                f"Option {configurable.name} has been set to {value}."
                if new_value is not None
                else f"Option {configurable.name} is currently set to {value}."
                f"\nUse {set_configurable_signature} to set it."
            )

            await ctx.send(
                embed=discord.Embed(title="Configuration", description=message)
            )
            return

        get_signature = wrap_in_code(f"{command} <option>")
        set_signature = wrap_in_code(f"{command} <option> <new value>")

        embed = discord.Embed(
            title="Configuration",
            description="Command to manage the bot's configuration for a server."
            f"\nTo get the value of an option use {get_signature}."
            f"\nTo set the value of an option use {set_signature}."
            "\nList of options can be found below:",
        )
        embed.set_footer(
            text="Page {current_page}/{total_pages}, "
            "showing option {first_field}..{last_field}/{total_fields}"
        )
        paginator = paginators.FieldPaginator(self.bot, base_embed=embed)

        for configurable in config.configurables:
            paginator.add_field(
                name=configurable.name.capitalize(),
                value=configurable.description,
            )

        await paginator.send(target=ctx.channel, owner=ctx.author)

    @commands.command()
    @commands.cooldown(3, 8, commands.BucketType.channel)
    async def about(self, ctx: commands.Context):
        """Gives information about this bot"""

        app_info = await self.bot.application_info()

        embed = discord.Embed(title="About", description=self.bot.description)

        embed.add_field(
            name="Links",
            value="[Support server](https://discohook.app/discord)"
            "\n[Invite link](https://discohook.app/bot)"
            "\n[Source code](https://github.com/discohook/bot)",
            inline=False,
        )

        embed.add_field(
            name="Owner",
            value=f"[{app_info.owner}](https://discord.com/users/{app_info.owner.id})",
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(3, 8, commands.BucketType.channel)
    async def invite(self, ctx: commands.Context):
        """Sends the bot invite and support server links"""

        await ctx.send(
            embed=discord.Embed(
                title="Invite",
                description="[Support server](https://discohook.app/discord)"
                "\n[Invite link](https://discohook.app/bot)",
            )
        )

    @commands.group(invoke_without_command=True)
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def data(self, ctx: commands.Context):
        """Commands to manage data stored by this bot"""
        await ctx.send_help("data")

    @data.command(name="delete")
    @commands.cooldown(3, 30, commands.BucketType.member)
    @commands.has_guild_permissions(administrator=True)
    async def data_delete(self, ctx: commands.Context):
        """Delete the server's data stored by this bot"""

        message = await ctx.send(
            embed=discord.Embed(
                title="Confirmation",
                description="Are you sure you want to delete all data for this"
                " server? This action cannot be reverted.\n\nTo ensure no data"
                " is kept, the bot will leave the server immediately. If you"
                " desire to keep me, you can reinvite me at"
                " https://discohook.app/bot.",
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
            await message.edit(
                embed=discord.Embed(
                    title="Confirmation cancelled",
                    description="30 second timeout reached",
                )
            )
            await message.remove_reaction("\N{WASTEBASKET}", ctx.guild.me)
            return

        await message.edit(
            embed=discord.Embed(
                title="Leaving server",
                description="Data will be deleted hereafter."
                " If you have any questions, please ask them in the"
                " [support server](https://discohook.app/discord).",
            )
        )

        await ctx.guild.leave()
        await self.cfg.delete_data(ctx.guild)

    @data.command(name="dump")
    @commands.cooldown(3, 30, commands.BucketType.member)
    @commands.has_guild_permissions(administrator=True)
    async def dump(self, ctx: commands.Context):
        """Dumps all data stored by this bot"""

        config = dict(await self.cfg.ensure(ctx.guild))

        reaction_roles = await self.db.fetch(
            """
            SELECT * FROM reaction_role
            WHERE guild_id = $1
            """,
            ctx.guild.id,
        )
        config["reaction_roles"] = [dict(row) for row in reaction_roles]

        fp = io.StringIO()
        json.dump(config, fp, indent=2)
        fp.seek(0)

        try:
            await ctx.author.send(
                embed=discord.Embed(
                    title="Data dump",
                    description=f"Data dump requested inside of {ctx.guild}.",
                ),
                file=discord.File(fp, filename=f"{ctx.guild.id}.json"),
            )
            await ctx.channel.send(
                embed=discord.Embed(
                    title="Data dump sent",
                    description="Please check your DMs.",
                )
            )
        except discord.Forbidden:
            await ctx.channel.send(
                embed=discord.Embed(
                    title="DM failed",
                    description="Could not send DM, check server privacy settings or unblock me.",
                )
            )


def setup(bot: commands.Bot):
    meta = Meta(bot)
    bot.add_cog(meta)
