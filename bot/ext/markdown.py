import io
from typing import Union

import discord
from bot import cmd, converter
from discord.ext import commands


class Markdown(cmd.Cog):
    """Markdown syntax helpers"""

    @commands.command(aliases=["member"])
    @commands.cooldown(4, 4, commands.BucketType.member)
    async def user(self, ctx: cmd.Context, *, member: discord.Member = None):
        """Gives formatting to mention a given member"""

        if member is None:
            member = ctx.author

        embed = discord.Embed(title="Syntax", description=f"`{member.mention}`")
        embed.add_field(name="Output", value=member.mention)
        embed.set_footer(text=f"ID: {member.id}")

        await ctx.prompt(embed=embed)

    @commands.command()
    @commands.cooldown(4, 4, commands.BucketType.member)
    @commands.guild_only()
    async def role(self, ctx: cmd.Context, *, role: discord.Role):
        """Gives formatting to mention a given role"""

        embed = discord.Embed(title="Syntax", description=f"`{role.mention}`")
        embed.add_field(name="Output", value=role.mention)
        embed.set_footer(text=f"ID: {role.id}")

        if role == ctx.guild.default_role:
            embed.add_field(
                name="Warning",
                value="This pings the '\\@everyone' role, not @everyone."
                " To ping everyone just write `@everyone`.",
            )

        await ctx.prompt(embed=embed)

    @commands.command()
    @commands.cooldown(4, 4, commands.BucketType.member)
    @commands.guild_only()
    async def channel(
        self,
        ctx: cmd.Context,
        *,
        channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel],
    ):
        """Gives formatting to link to a given text, voice, or stage channel"""

        embed = discord.Embed(title="Syntax", description=f"`{channel.mention}`")
        embed.add_field(name="Output", value=channel.mention)
        embed.set_footer(text=f"ID: {channel.id}")

        await ctx.prompt(embed=embed)

    @commands.command(aliases=["emote"])
    @commands.cooldown(4, 4, commands.BucketType.member)
    async def emoji(self, ctx: cmd.Context, *, emoji: converter.PartialEmojiConverter):
        """Gives formatting to use a given server emoji"""

        guild_emoji = self.bot.get_emoji(emoji.id)

        embed = discord.Embed(
            title="Syntax",
            description=f"`{emoji}`"
            if guild_emoji and guild_emoji.is_usable()
            else f"*`<`*`{'a' if emoji.animated else ''}:{emoji.name}:{emoji.id}>`",
        )
        embed.add_field(name="Output", value=str(emoji))
        embed.set_footer(text=f"ID: {emoji.id}")

        await ctx.prompt(embed=embed)

    @commands.command()
    @commands.cooldown(4, 4, commands.BucketType.member)
    async def raw(self, ctx: cmd.Context, *, content: str):
        """Returns the raw formatting of a message"""

        if "```" in content:
            fp = io.StringIO(content)
            await ctx.prompt(
                files=[discord.File(fp, filename=f"{ctx.message.id}.txt")],
                embed=discord.Embed(
                    title="Raw formatting",
                    description="Formatting could not be sent in chat "
                    "because the message contained a code block.",
                ),
            )
            return

        await ctx.prompt(
            embed=discord.Embed(
                title="Raw formatting",
                description=f"```\n{content}\n```",
            )
        )


def setup(bot):
    bot.add_cog(Markdown(bot))
