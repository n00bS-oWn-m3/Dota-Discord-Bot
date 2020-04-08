import discord
from discord.ext import commands
from itertools import cycle

# in case I forget the syntax of a cog, doesn't actually do something
class Example(commands.Cog):

    def __init__(self, bot):
        self.bot = bot # never forget this


    # EVENT inside cog
    @commands.Cog.listener()
    async def on_ready(self):
        print('Example cog is ready.')

    # COMMAND inside cog
    @commands.command()
    async def example(self, ctx):
        await ctx.send('This is an example.')


def setup(bot): # important for some reason (idk why)
    bot.add_cog(Example(bot))
