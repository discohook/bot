from discord.ext import commands

from .utils import converter


class Markdown(commands.Cog):
    """Markdown syntax helpers"""

    @commands.command()
    @commands.guild_only()
    async def user(
        self, ctx: commands.Context, member: converter.GuildMemberConverter,
    ):
        """Gives formatting to mention a given member"""

        await ctx.send(f"`{member.mention}`")

    @commands.command()
    @commands.guild_only()
    async def role(
        self, ctx: commands.Context, role: converter.GuildRoleConverter,
    ):
        """Gives formatting to mention a given role"""

        await ctx.send(f"`{role.mention}`")

    @commands.command()
    @commands.guild_only()
    async def channel(
        self, ctx: commands.Context, channel: converter.GuildTextChannelConverter,
    ):
        """Gives formatting to link to a given channel"""

        await ctx.send(f"`{channel.mention}`")

    @commands.command(aliases=["emote"])
    @commands.guild_only()
    async def emoji(
        self, ctx: commands.Context, emoji: converter.GuildEmojiConverter,
    ):
        """Gives formatting to use a given server emoji"""

        await ctx.send(f"`{emoji}`")


def setup(bot):
    bot.add_cog(Markdown(bot))
