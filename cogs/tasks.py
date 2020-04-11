import discord
from discord.ext import commands, tasks
from itertools import cycle


class Tasks(commands.Cog): # cog to define tasks.

    def __init__(self, bot): # make sure to do *function*.start() to start the task.
        self.bot = bot
        self.status = cycle(['Your Dota 2 Replays', 'A Well-Executed Fountain Hook', 'The Latest Patch Updates',
                             'You Lose, Again...', 'Sniper Being... Sniper', "'Supports' Taking Your Last-Hits",
                             'The PangoLove Spread', "GameLeap's 'Broken' Heroes Getting Trashed",
                             'Zeus Stealing Them Kills', 'You Win For A Change','Everyone Blaming The Supports',
                             'You Not Getting Any Last-Hits', "Naga Siren's Ultimate Doing Absolutely Nothing"])
        self.change_status.start()

    @tasks.loop(minutes=20.0)
    async def change_status(self):
        await self.bot.change_presence(status=discord.Status.idle, activity=discord.Activity(name=next(self.status)
                                                                                             , type=discord.ActivityType.watching))

    @change_status.before_loop
    async def change_status_before(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Tasks(bot))