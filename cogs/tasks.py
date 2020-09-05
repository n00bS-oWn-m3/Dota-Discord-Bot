import json

import discord
from discord.ext import commands, tasks
from discord.utils import get
from itertools import cycle
from cogs.scoring import cache
from helpers.constants import settings
from helpers.calculator import get_rank, scorecalc, average


async def update_roles(usermapping, guild_id, guild):
    # filter to only contain the mentions
    user_mentions = {}
    for y in usermapping[guild_id].items():
        if y[0][:2] == "<@":
            user_mentions[y[0]] = y[1]

    rank_dict = {}  # shows which rank every member deserves
    for user, steamid in user_mentions.items():
        score = round(average(scorecalc(steamid)), 2)
        discord_id = usermapping[guild_id][steamid]['discord_id']
        member = guild.get_member(discord_id)
        rank_dict[member] = get_rank(score)

    dev_role = get(guild.roles, name=settings["bot_dev_role"])
    for member, role in rank_dict.items():  # replace all roles with new ones
        # Note: 'Server Owner' and 'Dev' cannot be replaced
        if dev_role in member.roles:
            await member.edit(reason=f"{member} now is {role}", roles=[guild.default_role, dev_role, role])
        else:
            await member.edit(reason=f"{member} now is {role}", roles=[guild.default_role, role])


class Tasks(commands.Cog):  # cog to define tasks.

    def __init__(self, bot):  # make sure to do *function*.start() to start the task.
        self.bot = bot
        self.status = cycle(['Your Dota 2 Replays', 'A Well-Executed Fountain Hook', 'The Latest Patch Updates',
                             'You Lose, Again...', 'Sniper Being... Sniper', "'Supports' Taking Your Last-Hits",
                             'The PangoLove Spread', "GameLeap's 'Broken' Heroes Getting Trashed",
                             'Zeus Stealing Them Kills', 'You Win For A Change', 'Everyone Blaming The Supports',
                             'You Not Getting Any Last-Hits', "Naga Siren's Ultimate Doing Absolutely Nothing"])
        self.change_status.start()
        self.update_cache.start()

    @tasks.loop(hours=12.0)  # might want to change the interval
    async def update_cache(self):
        with open('resources/json_files/usermapping.json', 'r') as f:
            usermapping = json.load(f)

        # execute cache
        for guild_id in usermapping.keys():
            await cache(guild_id)
            guild = self.bot.get_guild(int(guild_id))
            await update_roles(usermapping, guild_id, guild)

    @update_cache.before_loop
    async def update_cache_before(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=20.0)
    async def change_status(self):
        await self.bot.change_presence(status=discord.Status.idle, activity=discord.Activity(name=next(self.status)
                                                                                             ,
                                                                                             type=discord.ActivityType.watching))

    @change_status.before_loop
    async def change_status_before(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Tasks(bot))