import re
from typing import Optional, Union

from discord.ext import commands

from bot import cmd


def wrap_in_code(value: str, *, block: Optional[Union[bool, str]] = None):
    value = value.replace("`", "\u200b`\u200b")
    value = value.replace("\u200b\u200b", "\u200b")

    if block is None:
        if "`" in value:
            return "``" + value + "``"
        return "`" + value + "`"

    lang = "" if block is True else block

    return f"```{block}\n" + value + "\n```"


def get_clean_prefix(ctx: cmd.Context):
    if re.match(f"<@!?{ctx.me.id}>", ctx.prefix):
        return f"@{ctx.me.display_name} "

    return ctx.prefix


def get_command_signature(
    ctx: cmd.Context,
    command: commands.Command,
    *,
    with_prefix=True,
    full=False,
):
    parent = command.full_parent_name
    names = command.name if not parent else parent + " " + command.name

    if full and len(command.aliases) > 0:
        name_with_aliases = f"[{command.name}|{'|'.join(command.aliases)}]"
        names = f"{parent} {name_with_aliases}" if parent else name_with_aliases

    signature = f"{get_clean_prefix(ctx)}{names}" if with_prefix else names
    if command.signature:
        signature += f" {command.signature}".replace("_", " ")

    return wrap_in_code(signature)
