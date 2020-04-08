import discord
from discord.ext import commands


class Errors(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please pass in all required arguments.")
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("I don't know what you mean by that.\nPlease use a valid command.")
        if isinstance(error, discord.Forbidden):
            await ctx.send("I don't have the required permissions to do as you please.")


def setup(bot):
    bot.add_cog(Errors(bot))
