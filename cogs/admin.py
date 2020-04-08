import discord
from discord.ext import commands
import json

class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot



#kicks and bans
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f'Successfully kicked **{member.mention}**.')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.send(f'Successfully banned **{member.mention}**.')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f"Succesfully unbanned **{user.mention}**.")
                return


# change prefix configurations (need to be a 'Dev')
    @commands.command()
    @commands.has_role('Dev')
    async def change_prefix(self, ctx, prefix):
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)
        prefixes[str(ctx.guild.id)] = prefix

        with open('prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)
        await ctx.send(f"Prefix changed to:   {prefix}")


def setup(bot):
    bot.add_cog(Admin(bot))