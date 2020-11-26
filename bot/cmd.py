from discord.ext import commands


class Cog(commands.Cog):
    def __init__(self, bot):
        super().__init__()

        self.bot = bot

    @property
    def loop(self):
        return self.bot.loop

    @property
    def db(self):
        return self.bot.pool

    @property
    def cfg(self):
        return self.bot.get_cog("Config")

    @property
    def session(self):
        return self.bot.session


class Context(commands.Context):
    def __init__(self, **attrs):
        super().__init__(**attrs)

        self.sent_message = None

    async def send(
        self,
        content=None,
        *,
        force_send=False,
        tts=False,
        embed=None,
        files=None,
        delete_after=None,
        nonce=None,
        allowed_mentions=None,
        suppress=False,
    ):
        if force_send:
            self.sent_message = None

        if self.sent_message:
            await self.sent_message.edit(
                content=content,
                embed=embed,
                delete_after=delete_after,
                allowed_mentions=allowed_mentions,
                suppress=suppress,
            )
            return self.sent_message

        self.sent_message = await super().send(
            content=content,
            tts=tts,
            embed=embed,
            files=files,
            delete_after=delete_after,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
        )
        return self.sent_message
