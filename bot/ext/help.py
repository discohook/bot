import itertools

import discord
from bot.utils import wrap_in_code
from discord.ext import commands


class HelpCommand(commands.HelpCommand):
    def __init__(self, **options):
        options.setdefault("verify_checks", False)
        options.setdefault("command_attrs", {}).setdefault(
            "help", "Shows help on how to use the bot and its commands"
        )

        super().__init__(**options)

    async def prepare_help_command(self, ctx, command=None):
        prefix = self.clean_prefix.replace(r"\\", "\\")
        command = f"{prefix}{self.invoked_with}"

        self.embed = discord.Embed(title="Help")
        self.embed.set_footer(text=f'Use "help" or "help <command>" for more info')

    def get_command_signature(self, command, *, short=False):
        parent = command.full_parent_name
        alias = command.name if not parent else parent + " " + command.name

        if not short and len(command.aliases) > 0:
            name_with_aliases = f"[{command.name}|{'|'.join(command.aliases)}]"
            alias = f"{parent} {name_with_aliases}" if parent else name_with_aliases

        signature = f"{self.context.prefix}{alias}" if not short else alias
        if command.signature:
            signature += f" {command.signature}".replace("_", " ")

        return wrap_in_code(signature)

    def command_not_found(self, string):
        return f"Command {wrap_in_code(string)} does not exist"

    def subcommand_not_found(self, command, string):
        return f"Command {wrap_in_code(command.qualified_name)} has no subcommand named {wrap_in_code(string)}"

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

        for category, commands in grouped:
            commands = sorted(commands, key=lambda command: command.name)
            description = []

            for command in commands:
                description.append(
                    f"{self.get_command_signature(command, short=True)}: {command.help}"
                )

            self.embed.add_field(
                name=category, value="\n".join(description), inline=False
            )

        await self.get_destination().send(embed=self.embed)

    async def send_cog_help(self, cog: commands.Cog):
        self.embed.title = f"Help: `{cog.qualified_name}`"
        self.embed.description = cog.description

        commands = await self.filter_commands(cog.get_commands(), sort=True)

        for command in commands:
            self.embed.add_field(
                name=f"{self.get_command_signature(command, short=True)}",
                value=command.short_doc,
                inline=False,
            )

        await self.get_destination().send(embed=self.embed)

    async def send_group_help(self, group: commands.Group):
        self.embed.title = f"Help: {self.get_command_signature(group)}"
        self.embed.description = group.help

        commands = await self.filter_commands(group.commands, sort=True)

        for command in commands:
            self.embed.add_field(
                name=f"{self.get_command_signature(command, short=True)}",
                value=command.short_doc,
                inline=False,
            )

        await self.get_destination().send(embed=self.embed)

    async def send_command_help(self, command: commands.Command):
        self.embed.title = f"Help: {self.get_command_signature(command)}"
        self.embed.description = command.help

        await self.get_destination().send(embed=self.embed)


def setup(bot: commands.Bot):
    bot.help_command = HelpCommand()
    bot.help_command.cog = bot.get_cog("Meta")


def teardown(bot: commands.Bot):
    bot.help_command = None
