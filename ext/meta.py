import asyncio
import collections
import itertools
import re
import typing

import discord
from discord.ext import commands
from discord.utils import get


class HelpCommand(commands.HelpCommand):
    async def prepare_help_command(self, ctx, command=None):
        prefix = self.clean_prefix.replace(r"\\", "\\")
        command = f"{prefix}{self.invoked_with}"

        self.embed = discord.Embed(title="Help")
        self.embed.set_footer(text=f'Use "{command} [command]" for more info')

    def get_command_signature(self, command, *, short=False):
        parent = command.full_parent_name
        alias = command.name if not parent else parent + " " + command.name

        if not short and len(command.aliases) > 0:
            name_with_aliases = f"[{command.name}|{'|'.join(command.aliases)}]"
            alias = f"{parent} {name_with_aliases}" if parent else name_with_aliases

        signature = f"{self.context.prefix}{alias}" if not short else alias
        if command.signature:
            signature += f" {command.signature}".replace("_", " ")

        return signature

    def command_not_found(self, string):
        return f'Command "{string}" does not exist'

    def subcommand_not_found(self, command, string):
        return f'Command "{command.qualified_name}" has no subcommand named "{string}"'

    async def send_error_message(self, error):
        await self.get_destination().send(
            embed=discord.Embed(title="Error", description=error)
        )

    async def send_bot_help(self, mapping):
        if self.context.bot.description:
            self.embed.description = self.context.bot.description

        grouped = itertools.groupby(
            await self.filter_commands(
                self.context.bot.commands,
                sort=True,
                key=lambda command: command.cog.qualified_name,
            ),
            key=lambda command: command.cog.qualified_name,
        )

        for category, commands in grouped:
            commands = sorted(commands, key=lambda command: command.name)
            description = []

            for command in commands:
                description.append(
                    f"`{self.get_command_signature(command, short=True)}`: {command.help}"
                )

            self.embed.add_field(
                name=category, value="\n".join(description), inline=False
            )

        await self.get_destination().send(embed=self.embed)

    async def send_cog_help(self, cog: commands.Cog):
        self.embed.title = f"Help: {cog.qualified_name}"

        if cog.description:
            self.embed.description = cog.description

        commands = await self.filter_commands(cog.get_commands(), sort=True)

        for command in commands:
            self.embed.add_field(
                name=f"`{self.get_command_signature(command, short=True)}`",
                value=command.short_doc,
                inline=False,
            )

        await self.get_destination().send(embed=self.embed)

    async def send_group_help(self, group: commands.Group):
        self.embed.title = f"Help: {group.qualified_name}"
        self.embed.description = (
            f"Syntax: `{self.get_command_signature(group)}`\n{group.help}"
        )

        commands = await self.filter_commands(group.commands, sort=True)

        for command in commands:
            self.embed.add_field(
                name=f"`{self.get_command_signature(command, short=True)}`",
                value=command.help,
                inline=False,
            )

        await self.get_destination().send(embed=self.embed)

    async def send_command_help(self, command: commands.Command):
        self.embed.title = f"Help: {command.qualified_name}"

        self.embed.description = (
            f"Syntax: `{self.get_command_signature(command)}`\n{command.help}"
        )

        await self.get_destination().send(embed=self.embed)


Configurable = collections.namedtuple(
    "Configurable", ["name", "description", "column", "type"]
)

configurables = [
    Configurable(
        name="prefix",
        description="Prefix specific to server, mention prefix will always work.",
        column="prefix",
        type=str,
    ),
    Configurable(
        name="private",
        description="Make certain sensitive commands private to server moderators.",
        column="commands_private",
        type=bool,
    ),
]

type_names = {str: "text", bool: "boolean", int: "number"}


class Meta(commands.Cog):
    """Commands related to the bot itself"""

    def __init__(self, bot):
        self.bot = bot

    def _resolve_value(self, expected_type, raw_value):
        type_name = type_names[expected_type]
        escaped_value = "``" + raw_value.replace("`", "\u200b`\u200b") + "``"

        if expected_type is bool:
            lowered = raw_value.lower()
            if lowered in ("yes", "y", "true", "t", "1", "enable", "on"):
                return True
            elif lowered in ("no", "n", "false", "f", "0", "disable", "off"):
                return False
            else:
                raise commands.BadArgument(
                    f"Value {escaped_value} is not a {type_name}"
                )
        else:
            try:
                return expected_type(raw_value)
            except:
                raise commands.BadArgument(
                    f"Value {escaped_value} is not a {type_name}"
                )

    async def _config_get(self, guild, configurable):
        return await self.bot.db.fetchval(
            """
            SELECT {} FROM guild_config
            WHERE guild_id = $1
            """.format(
                configurable.column
            ),
            guild.id,
        )

    async def _config_set(self, guild, configurable, new_value):
        await self.bot.db.execute(
            """
            UPDATE guild_config
            SET {} = $2
            WHERE guild_id = $1
            """.format(
                configurable.column
            ),
            guild.id,
            new_value,
        )

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
            configurable = get(configurables, name=option.lower())
            if configurable is None:
                raise commands.UserInputError(f'Option "{option}" not found')

            if new_value:
                await commands.has_guild_permissions(manage_guild=True).predicate(ctx)

                parsed_value = self._resolve_value(configurable.type, new_value)
                await self._config_set(ctx.guild, configurable, new_value)

            value = (
                new_value
                if new_value is not None
                else await self._config_get(ctx.guild, configurable)
            )
            value = (
                ("yes" if value else "no") if isinstance(value, bool) else str(value)
            )
            value = "``" + value.replace("`", "\u200b`\u200b") + "``"

            message = (
                f"Option {configurable.name} has been set to {value}."
                if new_value is not None
                else f"Option {configurable.name} is currently set to {value}."
                "\nUse `{command} {configurable.name} <new value>` to set it."
            )

            await ctx.send(
                embed=discord.Embed(title="Configuration", description=message)
            )
            return

        embed = discord.Embed(
            title="Configuration",
            description="Command to manage the bot's configuration for a server."
            f"\nTo get the value of an option use `{command} <option>`."
            f"\nTo set the value of an option use `{command} <option> <new value>`."
            "\nList of options can be found below:",
        )

        for configurable in configurables:
            embed.add_field(
                name=configurable.name.capitalize(),
                value=configurable.description,
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(3, 8, commands.BucketType.channel)
    async def about(self, ctx: commands.Context):
        """Gives information about this bot"""

        embed = discord.Embed(title="About", description=self.bot.description)
        embed.add_field(
            name="Privacy and Security",
            value="Want your data deleted? Use the `deletemydata` command to get more info."
            "\nHave a security issue? Join the support server and DM vivi#1111.",
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(3, 8, commands.BucketType.channel)
    async def invite(self, ctx: commands.Context):
        """Gives information about this bot"""

        await ctx.send(
            embed=discord.Embed(title="Invite", description=self.bot.description)
        )

    @commands.command()
    @commands.cooldown(3, 8, commands.BucketType.channel)
    async def deletemydata(self, ctx: commands.Context):
        """Gives information on how to delete your data"""

        await ctx.send(
            embed=discord.Embed(
                title="Delete my data",
                description="As of now, this bot stores zero data specific to users."
                "\nIf you are a server owner you can delete data specific to this guild by kicking or banning me.",
            )
        )


def setup(bot: commands.Bot):
    meta = Meta(bot)
    bot.add_cog(meta)
    bot.help_command = HelpCommand()
    bot.help_command.cog = meta
