import discord
from discord.ext import commands

from .utils import converter


class Markdown(commands.Cog):
    """Markdown syntax helpers"""

    @commands.command(aliases=["member"])
    @commands.guild_only()
    async def user(
        self, ctx: commands.Context, member: converter.GuildMemberConverter,
    ):
        """Gives formatting to mention a given member"""

        embed = discord.Embed(title="Syntax", description=f"`{member.mention}`")
        embed.add_field(name="Output", value=member.mention)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def role(
        self, ctx: commands.Context, role: converter.GuildRoleConverter,
    ):
        """Gives formatting to mention a given role"""

        embed = discord.Embed(title="Syntax", description=f"`{role.mention}`")
        embed.add_field(name="Output", value=role.mention)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def channel(
        self, ctx: commands.Context, channel: converter.GuildTextChannelConverter,
    ):
        """Gives formatting to link to a given channel"""

        embed = discord.Embed(title="Syntax", description=f"`{channel.mention}`")
        embed.add_field(name="Output", value=channel.mention)

        await ctx.send(embed=embed)

    @commands.command(aliases=["emote"])
    @commands.guild_only()
    async def emoji(
        self, ctx: commands.Context, emoji: converter.GuildEmojiConverter,
    ):
        """Gives formatting to use a given server emoji"""

        embed = discord.Embed(title="Syntax", description=f"`{emoji}`")
        embed.add_field(name="Output", value=str(emoji))

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Markdown(bot))
