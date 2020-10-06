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
        return self.bot.db

    @property
    def session(self):
        return self.bot.session
