import itertools

import discord
from bot.utils import get_clean_prefix, get_command_signature, paginators, wrap_in_code
from discord.ext import commands


class HelpCommand(commands.HelpCommand):
    def __init__(self, **options):
        options.setdefault("verify_checks", False)
        options.setdefault("command_attrs", {}).setdefault(
            "help", "Shows help on how to use the bot and its commands"
        )

        super().__init__(**options)

    async def prepare_help_command(self, ctx, command):
        prefix = get_clean_prefix(ctx)

        self.embed = discord.Embed(title="Help")
        self.embed.set_footer(
            text=f'Use "{prefix}help" or "{prefix}help <command>" for more info'
        )

    def get_paginator(self):
        embed = self.embed.copy()
        embed.set_footer(
            text=embed.footer.text + "\nPage {current_page}/{total_pages},"
            " showing module {first_field}..{last_field}/{total_fields}"
        )

        return paginators.FieldPaginator(self.context.bot, base_embed=embed)

    def get_command_signature(self, command, *, full=False):
        return get_command_signature(self.context, command, full=full)

    def command_not_found(self, string):
        return f"Command {wrap_in_code(string)} does not exist."

    def subcommand_not_found(self, command, string):
        return f"Command {wrap_in_code(command.qualified_name)} has no subcommand named {wrap_in_code(string)}."

    async def send_error_message(self, error):
        await self.get_destination().send(
            embed=discord.Embed(title="Error", description=error)
        )

    async def send_bot_help(self, mapping):
        self.embed.description = self.context.bot.description

        grouped = itertools.groupby(
            await self.filter_commands(
                self.context.bot.commands,
                sort=True,
                key=lambda command: command.cog.qualified_name,
            ),
            key=lambda command: command.cog.qualified_name,
        )

        paginator = self.get_paginator()

        for category, commands in grouped:
            commands = sorted(commands, key=lambda command: command.name)
            description = []

            for command in commands:
                description.append(
                    f"{self.get_command_signature(command)}: {command.help}"
                )

            paginator.add_field(
                name=category, value="\n".join(description), inline=False
            )

        await paginator.send(target=self.get_destination(), owner=self.context.author)

    async def send_cog_help(self, cog: commands.Cog):
        self.embed.title = f"Help: {cog.qualified_name}"
        self.embed.description = cog.description

        paginator = self.get_paginator()

        commands = await self.filter_commands(cog.get_commands(), sort=True)
        for command in commands:
            paginator.add_field(
                name=f"{self.get_command_signature(command)}",
                value=command.short_doc,
                inline=False,
            )

        await paginator.send(target=self.get_destination(), owner=self.context.author)

    async def send_group_help(self, group: commands.Group):
        self.embed.title = f"Help: {self.get_command_signature(group, full=True)}"
        self.embed.description = group.help

        paginator = self.get_paginator()

        commands = await self.filter_commands(group.commands, sort=True)
        for command in commands:
            paginator.add_field(
                name=f"{self.get_command_signature(command)}",
                value=command.short_doc,
                inline=False,
            )

        await paginator.send(target=self.get_destination(), owner=self.context.author)

    async def send_command_help(self, command: commands.Command):
        self.embed.title = f"Help: {self.get_command_signature(command, full=True)}"
        self.embed.description = command.help

        await self.get_destination().send(embed=self.embed)


def setup(bot: commands.Bot):
    bot.help_command = HelpCommand()
    bot.help_command.cog = bot.get_cog("Meta")


def teardown(bot: commands.Bot):
    bot.help_command = None
