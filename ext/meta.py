import asyncio
import itertools
import re

import discord
from discord.ext import commands


class HelpCommand(commands.HelpCommand):
    async def prepare_help_command(self, ctx, command=None):
        prefix = self.clean_prefix.replace(r"\\", "\\")
        command = f"{prefix}{self.invoked_with}"

        self.embed = discord.Embed(title="Help")
        self.embed.set_footer(text=f'Use "{command} [command]" for more info')

    def get_command_signature(self, command):
        parent = command.full_parent_name
        alias = command.name if not parent else parent + " " + command.name

        if len(command.aliases) > 0:
            name_with_aliases = f"[{command.name}|{'|'.join(command.aliases)}]"
            alias = f"{parent} {name_with_aliases}" if parent else name_with_aliases

        return f"{self.context.prefix}{alias} {command.signature}"

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

        def get_category(command):
            return command.cog.qualified_name if command.cog is not None else "Meta"

        grouped = itertools.groupby(
            await self.filter_commands(
                self.context.bot.commands, sort=True, key=get_category,
            ),
            key=get_category,
        )

        for category, commands in grouped:
            commands = sorted(commands, key=lambda command: command.name)
            description = []

            for command in commands:
                description.append(f"`{command.name}`: {command.short_doc}")

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
                name=f"`{command.name}`", value=command.short_doc, inline=False
            )

        await self.get_destination().send(embed=self.embed)

    async def send_group_help(self, group: commands.Group):
        self.embed.title = f"Help: {group.qualified_name}"

        description = f"Syntax: {self.get_command_signature(group)}"
        if group.description:
            description += "\n" + group.description
        if group.help:
            description += "\n" + group.help

        self.embed.description = description

        commands = await self.filter_commands(group.commands, sort=True)

        for command in commands:
            self.embed.add_field(
                name=f"`{group.qualified_name} {command.name}`",
                value=command.short_doc,
                inline=False,
            )

        await self.get_destination().send(embed=self.embed)

    async def send_command_help(self, command: commands.Command):
        self.embed.title = f"Help: {command.qualified_name}"

        description = f"Syntax: {self.get_command_signature(command)}"
        if command.description:
            description += "\n" + command.description
        if command.help:
            description += "\n" + command.help

        self.embed.description = description

        await self.get_destination().send(embed=self.embed)


class Meta(commands.Cog):
    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def prefix(self, ctx: commands.Context):
        """Manages the server prefix"""

        prefix = ctx.bot.prefixes.get(ctx.guild.id, "d.")
        await ctx.send(
            embed=discord.Embed(
                title="Prefix",
                description=f'The prefix for Discobot in this server is "{prefix}"',
            )
        )

    @prefix.command(name="set")
    async def prefix_set(self, ctx: commands.Context, prefix: str):
        """Sets the server prefix"""

        ctx.bot.prefixes.put(ctx.guild.id, prefix)

        await ctx.send(
            embed=discord.Embed(
                title="Prefix set",
                description=f'The prefix for this server is now "{prefix}"',
            )
        )


def setup(bot: commands.Bot):
    meta = Meta(bot)
    bot.add_cog(meta)
    bot.help_command = HelpCommand()
    bot.help_command.cog = meta
