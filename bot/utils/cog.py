from discord.ext import commands


class Cog(commands.Cog):
    def __init__(self, bot):
        super().__init__()

        self.bot = bot

    @property
    def loop(self):
        return self.bot.loop

    @property
    def cfg(self):
        return self.bot.get_cog("Config")

    @property
    def db(self):
        return self.cfg.pool

    @property
    def session(self):
        return self.bot.session
