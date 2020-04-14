from discord.ext import commands
import random


class Trivia(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Shows the ping of the bot.", description="Shows the ping of the bot.")
    async def ping(self, ctx):
        await ctx.send(f'Pong! {round(self.bot.latency * 1000)} ms')

    @commands.command(name='8ball', brief='In a doubt? Ask me!', description="If you're ever in a doubt, don't hesitate to question me!\nI'll enlighten you with my opinion!")
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

    @commands.command(brief="Clear a given amount of messages from the channel.")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount=1):
        await ctx.channel.purge(limit= amount + 1)

    @commands.command(hidden=True)
    async def poll(self, ctx, *, message):
        """
        Still needs some fixing.
        Can be used to get the reactions (yes / no) on a specific question.
        To-do: enable the bot to read the changed reactions
        """
        message = await ctx.send(message)
        emojis = ['✅', '❌']
        for emoji in emojis:
            await message.add_reaction(emoji)
        res = await self.bot.wait_for_reaction(emoji=emojis, message=message)
        if res:
            print("Reaction received")

def setup(bot):
    bot.add_cog(Trivia(bot))
