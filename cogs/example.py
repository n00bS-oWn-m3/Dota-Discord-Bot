import discord
from discord.ext import commands
from itertools import cycle

# In case I forget the syntax of a cog, doesn't actually do anything
class Example(commands.Cog):

    # Never forget this
    def __init__(self, bot):
        self.bot = bot 


    # EVENT inside of the cog
    @commands.Cog.listener()
    async def on_ready(self):
        print('Example cog is ready.')

    # COMMAND inside of the cog
    @commands.command()
    async def example(self, ctx):
        await ctx.send('This is an example.')


# Important for some reason, but I don't know why
def setup(bot): 
    bot.add_cog(Example(bot))
