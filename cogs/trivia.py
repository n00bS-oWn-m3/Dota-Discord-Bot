import discord
from discord.ext import commands
import random


class Trivia(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f'Pong! {round(self.bot.latency * 1000)} ms')

    @commands.command(aliases=['8ball'])
    async def _8ball(self, ctx, *, question=None):
        responses = ['As I see it, yes.',
                        'Ask again later.',
                       'Better not tell you now.',
                       'Cannot predict now.',
                       'Concentrate and ask again.',
                       'Don’t count on it.',
                       'It is certain.',
                       'It is decidedly so.',
                       'Most likely.',
                       'My reply is no.',
                       'My sources say no.',
                       'Outlook not so good.',
                       'Outlook good.',
                       'Reply hazy, try again.',
                       'Signs point to yes.',
                       'Very doubtful.',
                       'Without a doubt.',
                       'Yes.',
                       'Yes – definitely.',
                       'You may rely on it.']
        if question is None:
            await ctx.send('What question will you have me answered?')
        else:
            await ctx.send(f'Question: {question}\nAnswer: {random.choice(responses)}')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount=1):
        await ctx.channel.purge(limit= amount + 1)



def setup(bot):
    bot.add_cog(Trivia(bot))
