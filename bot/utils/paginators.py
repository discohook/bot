import asyncio
import typing

import discord
from discord.ext import commands

action_first = "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}"
action_previous = "\N{BLACK LEFT-POINTING TRIANGLE}"
action_next = "\N{BLACK RIGHT-POINTING TRIANGLE}"
action_last = "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}"


class FieldPaginator:
    def __init__(
        self,
        bot: commands.Bot,
        *,
        base_embed: discord.Embed = discord.Embed(),
    ):
        self.bot = bot
        self.base_embed = base_embed.copy()
        self.pages = [[]]

    def add_field(self, *, name: str, value: str, inline: bool = True):
        last_page = self.pages[-1]
        if len(last_page) >= 25 - len(self.base_embed.fields):
            last_page = []
            self.pages.append(last_page)

        last_page.append({"name": name, "value": value, "inline": inline})

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

    async def send(
        self,
        *,
        target: discord.abc.Messageable,
        owner: discord.User,
    ):
        message = await target.send(embed=self.get_embed_for_page(0))

        if len(self.pages) <= 1:
            return message

        self.bot.loop.create_task(self.loop(message=message, owner=owner))

        for reaction in [action_first, action_previous, action_next, action_last]:
            try:
                await message.add_reaction(reaction)
            except (discord.Forbidden, discord.NotFound):
                pass

        return message

    async def loop(
        self,
        *,
        message: discord.Message,
        owner: discord.User,
    ):
        page = 0

        async def set_page(index):
            page = max(0, min(len(self.pages), index))
            await message.edit(embed=self.get_embed_for_page(page))

        actions = {
            action_first: lambda: set_page(0),
            action_previous: lambda: set_page(page - 1),
            action_next: lambda: set_page(page + 1),
            action_last: lambda: set_page(len(self.pages) - 1),
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
                    "raw_reaction_add", check=check, timeout=60.0
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
