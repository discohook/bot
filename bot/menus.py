import asyncio
import typing

import discord
from discord.ext import commands

from bot import cmd


class FieldPaginator:
    action_first = "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}"
    action_previous = "\N{BLACK LEFT-POINTING TRIANGLE}"
    action_next = "\N{BLACK RIGHT-POINTING TRIANGLE}"
    action_last = "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}"

    def __init__(
        self,
        bot: commands.Bot,
        *,
        base_embed: discord.Embed = discord.Embed(),
    ):
        self.bot = bot
        self.base_embed = base_embed.copy()
        self.pages = [[]]

    def _should_create_new_page(self, *, page, name, value):
        page_field_limit = 25 - len(self.base_embed.fields)
        if len(page) >= page_field_limit:
            return True

        current_page_length = len(self.base_embed)
        for field in page:
            current_page_length += len(field["name"]) + len(field["value"])

        if current_page_length + len(name) + len(value) > 6000:
            return True

        return False

    def add_field(self, *, name: str, value: str, inline: bool = True):
        current_page = self.pages[-1]

        if self._should_create_new_page(page=current_page, name=name, value=value):
            current_page = []
            self.pages.append(current_page)

        current_page.append(
            {
                "name": name,
                "value": value,
                "inline": inline,
            }
        )

    def get_embed_for_page(self, index: int):
        embed = self.base_embed.copy()

        for field in self.pages[index]:
            embed.add_field(**field)

        if embed.footer.text != discord.Embed.Empty:
            embed.set_footer(
                text=embed.footer.text.format(
                    current_page=index + 1,
                    total_pages=len(self.pages),
                    first_field=sum(len(page) for page in self.pages[:index]) + 1,
                    last_field=sum(len(page) for page in self.pages[: index + 1]),
                    total_fields=sum(len(page) for page in self.pages),
                ),
                icon_url=embed.footer.icon_url,
            )

        return embed

    async def send(self, ctx: cmd.Context):
        message = await ctx.send(embed=self.get_embed_for_page(0))

        if len(self.pages) <= 1:
            return message

        self.bot.loop.create_task(self.loop(message=message, owner=ctx.author))

        for reaction in [
            self.action_first,
            self.action_previous,
            self.action_next,
            self.action_last,
        ]:
            try:
                await message.add_reaction(reaction)
            except (discord.Forbidden, discord.NotFound):
                pass

        return message

    async def loop(self, *, message: discord.Message, owner: discord.User):
        page = 0

        async def set_page(index):
            page = max(0, min(len(self.pages), index))
            await message.edit(embed=self.get_embed_for_page(page))

        actions = {
            self.action_first: lambda: set_page(0),
            self.action_previous: lambda: set_page(page - 1),
            self.action_next: lambda: set_page(page + 1),
            self.action_last: lambda: set_page(len(self.pages) - 1),
        }

        def check(event: discord.RawReactionActionEvent):
            return (
                event.user_id == owner.id
                and event.message_id == message.id
                and str(event.emoji) in actions
            )

        try:
            while not self.bot.is_closed():
                event = await self.bot.wait_for(
                    "raw_reaction_add", check=check, timeout=300.0
                )

                action = actions[str(event.emoji)]
                await action()

                try:
                    await message.remove_reaction(str(event.emoji), owner)
                except discord.Forbidden:
                    pass

        except (asyncio.TimeoutError, asyncio.CancelledError):
            for emoji in actions.keys():
                try:
                    await self.message.remove_reaction(emoji, self.bot.user)
                except (discord.Forbidden, discord.NotFound):
                    pass


class ConfirmationPrompt:
    action_confirm = '\N{WHITE HEAVY CHECK MARK}'
    action_deny = '\N{WHITE HEAVY CROSS MARK}'

    def __init__(
        self,
        bot: commands.Bot,
        *,
        embed: discord.Embed = discord.Embed(),
    ):
        self.bot = bot
        self.embed = embed.copy()

    async def send(self, ctx: cmd.Context):
        message = await ctx.prompt(embed=self.embed)

        if len(self.pages) <= 1:
            return message

        actions = {
            self.action_confirm: True,
            self.action_deny: False,
        }

        for reaction in actions.keys():
            try:
                await message.add_reaction(reaction)
            except (discord.Forbidden, discord.NotFound):
                pass

        def check(event: discord.RawReactionActionEvent):
            return (
                event.user_id == ctx.author.id
                and event.message_id == message.id
                and str(event.emoji) in actions
            )

        try:
            event = await self.bot.wait_for("raw_reaction_add", check=check, timeout=60.0)

            try:
                await message.remove_reaction(str(event.emoji), ctx.author)
            except discord.Forbidden:
                pass

            return actions[str(event.emoji)]

        except asyncio.TimeoutError:
            return False

        finally:
            for emoji in actions.keys():
                try:
                    await self.message.remove_reaction(emoji, self.bot.user)
                except (discord.Forbidden, discord.NotFound):
                    pass
