# Importing the required libraries
import aiohttp
import discord
from discord.ext import commands
from cogs.scoring import get_json, fetch, timer_converter

# Loading relevant data from JSON files
usermapping = get_json('usermapping.json')  # information about registered users


# Setting up the cog
class Aghanim(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # 
    @commands.command(brief="See your personal top runs of Aghanim's labyrinth",
                      description="See your personal top runs of Aghanim's labyrinth. Alternatively, specify a user to see their top runs")
    async def aghanim(self, ctx, user=None):

        # Setting up a few variables
        victories = 0
        durations = []
        times_text = ""

        # This entire block of code should be a function since we're using it fairly frequently and it's well written
        guild_id = str(ctx.guild.id)

        if user is None:  # get author of message
            user = ctx.message.author.mention
        try:
            steamid = usermapping[guild_id][f'{user}']
        except KeyError:
            await ctx.send("User isn't registered.")
            return

            # Gets the number of attempts a player has made at the event
        async with aiohttp.ClientSession() as session:
            attempts = len(await fetch(
                session, f"https://api.opendota.com/api/players/{steamid}/matches/?significant=0&game_mode=19"))

        # Fetches all won event games
        async with aiohttp.ClientSession() as session:
            wins = await fetch(
                session, f"https://api.opendota.com/api/players/{steamid}/matches/?significant=0&game_mode=19&win=1")

        for i in range(len(wins)):
            durations.append(wins[i]["duration"])

        times = sorted(durations)[:3]

        for i in range(len(times)):
            times[i] = timer_converter(times[i])

        while len(times) < 3:
            times.append("N/A")

        for i in range(len(times)):
            times_text = times_text + (times[i] + "\n")

        # Calculates the amount of wins and losses
        victories = len(wins)

        embed = discord.Embed(title="**Top Aghanim's Labyrinth runs**",
                              description=f"{user} has made {attempts} attempts at clearing Aghanim's labyrinth and has succeeded {victories} times.",
                              color=2248687)
        embed.set_thumbnail(
            url="https://gamepedia.cursecdn.com/dota2_gamepedia/5/52/Emoticon_aghs_scepter.gif?version=debd22106c9fa7874e2ee80cb9246eff")
        embed.add_field(name="**Top 3**", value="**1.**\n**2.**\n**3.**\n", inline=True)
        embed.add_field(name="Time", value=times_text, inline=True)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Aghanim(bot))
