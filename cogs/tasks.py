import discord
from discord.ext import commands, tasks
from itertools import cycle


class Tasks(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.status = cycle(['Your Dota 2 Replays', 'A Well-Executed Fountain Hook', 'The Latest Patch Updates',
                             'You Lose, Again...', 'Sniper Being... Sniper', "'Supports' Taking Your Last-Hits",
                             'The PangoLove Spread', "GameLeap's 'Broken' Heroes Getting Trashed",
                             'Zeus Stealing Them Kills', 'You Win For A Change','Everyone Blaming The Supports',
                             'You Not Getting Any Last-Hits', "Naga Siren's Ultimate Doing Absolutely Nothing"])
        self.change_status.start()

    @tasks.loop(seconds=10.0)
    async def change_status(self):
        self.bot.change_presence(status=discord.Status.idle, activity=discord.Activity(name=next(self.status)))


def setup(bot):
    bot.add_cog(Tasks(bot))