# Importing the required libraries
import datetime
import os
import requests
import time
import discord
from discord.ext import commands
import json


# Defining a function to quickly calculate the average of a list
def average(list):
    return sum(list) / len(list)


# A dictionary of our account ID's
with open('resources/json_files/usermapping.json', 'r') as f:
    usermapping = json.load(f)

# A dictionary of all game modes
with open('resources/json_files/game_mode.json', 'r') as f:
    game_modes = json.load(f)

# A dictionary of all lobby types
with open('resources/json_files/lobby_type.json', 'r') as f:
    lobby_types = json.load(f)

# All ranks with extra information
with open('resources/json_files/rankings.json', 'r') as f:
    rankings = json.load(f)

# Retrieves a match, whether it's cached or not


def get_match(match_id):
    if os.path.isfile(f"resources/cached_matches/{match_id}.json"):
        with open(f"resources/cached_matches/{match_id}.json", 'r') as f:
            return json.load(f)
    else:
        return requests.get(f'https://api.opendota.com/api/matches/{match_id}').json()

# request a parse by specific match-id


async def send_parse_request(match_id):
    requests.post(f'https://api.opendota.com/api/request/{match_id}')

# check if a game is already parsed


def is_parsed(match):
    return match.get('version', None) is not None

# convert the time in seconds to a nice string (up to hours, since I don't reckon any dota game will be any longer)


def timer_converter(seconds: int):
    seconds = abs(seconds)
    if seconds == 0:
        return "the start of the game"
    times = [
        ["{t} second{s}", 60],
        ["{t} minute{s}", 60],
        ["{t} hour{s}", 24]
    ]
    result = []
    divisor = 1
    for time in times:
        t = int((seconds // divisor) % time[1])
        if t > 0:
            result.insert(0, time[0].format(t=t, s="s" if t > 1 else ""))
        divisor *= time[1]

    # very ugly if-statement, but for now, it must do
    if len(result) == 3:  # up to hours
        return f"{result[0]}, {result[1]} and {result[2]}"
    elif len(result) == 2:  # up to minutes
        return f"{result[0]} and {result[1]}"
    elif len(result) == 1:  # up to seconds
        return f"{result[0]}"


def average_benchmarks_single_match(player):
    bench_list = []
    for i in player['benchmarks'].values():
        bench_list.append(i['pct'])
    return round(average(bench_list) * 100, 2)


# DOTA2 Constants
HEROES = (requests.get("https://api.opendota.com/api/constants/heroes")).json()


# Setting up a class
# All it needs is a name from the hardcoded dictionary, amount of games to analyze and whether to print out individual match data are optional arguments
class Scorecalc:

    def __init__(self, user, game_requests=5, debug=0):
        # Making empty variables and other setup
        self.recent = []
        self.benchmarks = []
        self.unparsed_matches = 0
        self.abandons = 0
        self.attempts = 0
        self.unparsed_old_matches = 0

        self.account_id = usermapping[f'{user}']
        self.game_requests = game_requests
        self.debug = debug

    def calculate(self):
        # Start of the main loop
        with open("resources/json_files/tracked_matches.json", 'r') as f:
            self.tracked_matches = json.load(f)

        if len(self.tracked_matches[self.account_id]) < self.game_requests:
            self.game_requests = len(self.tracked_matches[self.account_id])
        while len(self.recent) < self.game_requests:

            self.workable = True

            #
            self.match_id = self.tracked_matches[str(
                self.account_id)][self.attempts]
            with open(f"resources/cached_matches/{self.match_id}.json", 'r') as f:
                self.generaldata = json.load(f)
            self.matchdata = self.generaldata['players']

            # Increments the attempts variable by one, it's used to always go back one game
            self.attempts = self.attempts + 1

            # Checks if any players have abandoned the game
            for self.player_slot in range(10):
                if self.matchdata[self.player_slot]['leaver_status'] >= 2:
                    self.abandons += 1
                    self.workable = False
                break

            # Gets the data of the requested user
            self.player = next((p for p in self.matchdata if str(
                p['account_id']) == self.account_id), None)

            if self.workable == True:
                # Saving the hero id to a variable
                self.hero_id = self.player['hero_id']

                # Storing all relevant benchmarks in a list
                for i in self.player['benchmarks'].values():
                    self.benchmarks.append(i['pct'])

                # Calculating the score and appending it to a list
                # Currently does work, thanks to Sebastiaan
                self.recent.append(average(self.benchmarks) * 100)

                # Printing out some simple data
                if self.debug >= 2:
                    print(f"Match ID: {self.match_id}")
                    print(
                        f"Hero: {HEROES[f'{self.hero_id}']['localized_name']}")
                    print(
                        f"Score: {round(self.recent[len(self.recent) - 1], 3)}")
                    print()


# Setting up the Scoring cog
class Scoring(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # return a nice embed of a requested match
    @commands.command(brief="Information of a match by a given ID", description="Information of a match by a given ID")
    async def match(self, ctx, match_id,  user=None):
        match = get_match(match_id)
        if match == {"error": "Not Found"}:
            await ctx.send("Please use a valid match-id.")
        if not is_parsed(match):
            await ctx.send("Match isn't parsed yet. Please retry in a few moments.")
            await ctx.send("⏳ Requesting a parse...", delete_after=5)
            await send_parse_request(match_id)
        if user is None:  # get author of message
            user = ctx.message.author.mention
        try:
            steamid = usermapping[f'{user}']
        except KeyError:
            await ctx.send("User isn't registered.")
            return
        player = next((p for p in match['players'] if str(
            p['account_id']) == steamid), None)
        if player is None:  # didn't find any matching account_id
            await ctx.send(f"{user} doesn't seem to be a player in this game.")
            return

        # notify if there were any abandons and/or if the game mode is considered unbalanced
        warning_necessary = False
        warning_notice = "> The game's statistics might be conflicting with reality due to:"
        for p in match['players']:
            if p['leaver_status'] >= 2:
                warning_notice += "\n> --> Abandons"
                warning_necessary = True
                break
        if not game_modes[str(player['game_mode'])]['balanced']:
            warning_notice += "\n> --> Unbalanced Game-mode"
            warning_necessary = True
        if not lobby_types[str(player['lobby_type'])]['balanced']:
            warning_notice += "\n> --> Unbalanced lobby-type"
            warning_necessary = True

        # data to create our intro
        hero = HEROES[str(player['hero_id'])]
        hero_name = hero['localized_name']
        hero_icon = f"http://cdn.dota2.com{hero['icon']}"
        duration = timer_converter(player['duration'])
        victory_status = "Lost" if player['win'] == 0 else "Won"
        game_mode = game_modes[str(player['game_mode'])]['name']
        game_mode_prefix = "an" if game_mode[0] in "aeiouAEIOU" else "a"

        intro = (f"{victory_status} {game_mode_prefix} **{game_mode}** match as {hero_name} in {duration}.\n"
                 f"More information on [DotaBuff](https://www.dotabuff.com/matches/{match_id}), "
                 f"[OpenDota](https://www.opendota.com/matches/{match_id}) or "
                 f"[STRATZ](https://www.stratz.com/match/{match_id})")

        # calculating average score + indication of how well you played
        average_score = average_benchmarks_single_match(player)
        obtained_rank = ""

        for key in rankings:  # calculating the rank
            if rankings[key]['Demotion upon'] < average_score < rankings[key]['Promotion upon']:
                obtained_rank = key
                break

        rank_prefix = "an" if obtained_rank[0] in "aeiouAEIOU" else "a"
        playstyle_indication = (
            f">>> With a Score of **{average_score} %**, you played like {rank_prefix} **{obtained_rank}**")

        # the actual embed
        embed = discord.Embed(description=intro, color=297029,
                              timestamp=datetime.datetime.utcfromtimestamp(match['start_time']))
        embed.set_author(name=player['personaname'] or "Anonymous",
                         icon_url=hero_icon, url=f"https://www.opendota.com/players/{steamid}")
        bm = player['benchmarks']

        # adding warning message, if necessary
        if warning_necessary:
            embed.add_field(name="**Warning**",
                            value=warning_notice, inline=False)

        # adding the playstyle-indication
        embed.add_field(name=obtained_rank + " Player",
                        value=playstyle_indication, inline=False)

        # benchmarks headers
        bench_first = ("**Gold**:\n""**Experience**:\n**Kills**:\n**Last Hits**:\n**Hero Damage**:\n"
                       "**Hero Healing**:\n**Tower Damage**:\n**Stuns**:\n**Last Hits @ 10**:\n")
        # benchmarks raw stats
        bench_second = (f"{round(bm['gold_per_min']['raw'], 2)}\n{round(bm['xp_per_min']['raw'], 2)}\n{player['kills']}\n"
                        f"{player['last_hits']}\n{round(bm['hero_damage_per_min']['raw'], 2)}\n{round(bm['hero_healing_per_min']['raw'], 2)}\n"
                        f"{round(bm['tower_damage']['raw'], 2)}\n{round(player['stuns'], 2)}\n{round(bm['lhten']['raw'], 2)}\n")
        # benchmarks percentage stats
        bench_third = (f"{round(bm['gold_per_min']['pct'] * 100, 2)} %\n{round(bm['xp_per_min']['pct'] * 100, 2)} %\n"
                       f"{round(bm['kills_per_min']['pct'] * 100, 2)} %\n{round(bm['last_hits_per_min']['pct'] * 100, 2)} %\n"
                       f"{round(bm['hero_damage_per_min']['pct'] * 100, 2)} %\n{round(bm['hero_healing_per_min']['pct'] * 100, 2)} %\n"
                       f"{round(bm['tower_damage']['pct'] * 100, 2)} %\n{round(bm['stuns_per_min']['pct'] * 100, 2)} %\n"
                       f"{round(bm['lhten']['pct'] * 100, 2)} %\n")

        # adding benchmarks stats as 2 fields
        embed.add_field(name="**Benchmarks**", value=bench_first, inline=True)
        embed.add_field(name="Values", value=bench_second, inline=True)
        embed.add_field(name="Scores", value=bench_third, inline=True)

        # adding a thumbnail with the corresponding rank icon
        rank_icon = f"{obtained_rank.lower()}.png"
        embed.set_thumbnail(url=f"attachment://{rank_icon}")

        # adding a footer with the match-id (plus the timestamp from the match (see above))
        embed.set_footer(text=str(match_id))

        # have to do this to be able to import a local (resources/ranks_images) image
        icon = discord.File(f"resources/ranks_images/{rank_icon}", rank_icon)
        await ctx.send(embed=embed, file=icon)

    @commands.command(brief="Information about your last match.",
                      description="Information about your last match.\nWhen specifying the amount to be skipped, be sure to specify the user.")
    async def lastmatch(self, ctx, user=None, skip=0):
        # might want to fix this copy of code
        if user is None:  # get author of message
            user = ctx.message.author.mention
        try:
            steamid = usermapping[f'{user}']
        except KeyError:
            await ctx.send("User isn't registered.")
            return

        lastmatch = (requests.get(
            f"https://api.opendota.com/api/players/{steamid}/matches/?limit=1&offset={skip}")).json()
        lastmatch_id = lastmatch[0]['match_id']

        await self.match(ctx, lastmatch_id, user=user)

    @commands.command(brief="Get the average score of a given amount of games.",
                      description="Get the average score of a given amount of games.\n"
                                  "Debug options:\n  1: Additional information (abandons & parses).\n"
                                  "  2: Additional information printed to the terminal.")
    async def score(self, ctx, user=None, game_requests=25, debug=0):

        if user is None:  # get author of message
            user = ctx.message.author.mention
        try:
            steamid = usermapping[f'{user}']
        except KeyError:
            await ctx.send("User isn't registered.")
            return

        score = Scorecalc(f'{user}', game_requests, debug)

        score.calculate()

        await ctx.send(f"Average over {len(score.recent)} games: {round(average(score.recent),3)}")

        if len(score.recent) < game_requests:
            await ctx.send(f"I could only find {len(score.recent)} valid games to process instead of the requested {game_requests}.")

        if score.debug >= 1:
            if score.abandons == 1:
                await ctx.send(f"{score.abandons} match was abandoned by someone, it was not taken into consideration.")
            elif score.abandons > 1:
                await ctx.send(f"{score.abandons} matches were abandoned by someone, they were not taken into consideration.")

    @commands.command(brief="Link your Discord account to your Steam-ID.", description="Link your Discord account to your Steam-ID.")
    @commands.has_permissions(administrator=True)
    async def register(self, ctx, user, id):

        if len(id) != 9 or isinstance(id, int):
            await ctx.send("Please use the last part of a valid SteamID3.")

        else:
            usermap = {f'{user}': f'{id}'}

            with open('resources/json_files/usermapping.json') as f:
                data = json.load(f)

            data.update(usermap)

            with open('resources/json_files/usermapping.json', 'w') as f:
                json.dump(data, f, indent=4)

            await ctx.send(f"User {user} registered with Steam ID {id}.")

    @commands.command(brief="Cache recent matches.")
    async def cache(self, ctx, limit=50, offset=0):

        if os.path.isfile(f"resources/json_files/tracked_matches.json"):
            with open('resources/json_files/tracked_matches.json', 'r') as f:
                tracked_matches = json.load(f)
        else:
            tracked_matches = {}

        request = 0
        unparsed = 0

        # Removes duplicates from the list
        # This looks horrible, there has to be a better way to do this?
        steam_ids = list(dict.fromkeys(list(usermapping.values())))

        for account_id in steam_ids:
            if os.path.isfile(f"resources/json_files/tracked_matches.json"):
                match_list = tracked_matches[account_id]
            else:
                match_list = []

            matches = (requests.get(
                f"https://api.opendota.com/api/players/{account_id}/matches/?limit={limit}&offset={offset}")).json()

            while matches == {'error': 'rate limit exceeded'}:
                print('The rate limit was passed')
                time.sleep(5)
                matches = (requests.get(
                    f"https://api.opendota.com/api/players/{account_id}/matches/?limit={limit}&offset={offset}")).json()

            for i in range(len(matches)):
                if not os.path.isfile(f"resources/cached_matches/{matches[i]['match_id']}.json") and game_modes[str(matches[i]['game_mode'])]['balanced'] and lobby_types[str(matches[i]['lobby_type'])]['balanced']:

                    matchdata = (requests.get(
                        f"https://api.opendota.com/api/matches/{matches[i]['match_id']}")).json()
                    request += 1
                    while matchdata == {'error': 'rate limit exceeded'}:
                        print('The rate limit was passed')
                        time.sleep(5)
                        matchdata = (requests.get(
                            f"https://api.opendota.com/api/matches/{matches[i]['match_id']}")).json()

                    if is_parsed(matchdata):
                        match_list.append(matches[i]['match_id'])

                        with open(f"resources/cached_matches/{matches[i]['match_id']}.json", 'w') as jsonFile:
                            json.dump(matchdata, jsonFile)
                    else:
                        unparsed += 1
                else:
                    match_list.append(matches[i]['match_id'])

            tracked_matches[account_id] = match_list
            print(f"Done with {account_id}")

        with open(f"resources/json_files/tracked_matches.json", 'w') as jsonFile:
            json.dump(tracked_matches, jsonFile)
        print("Done with everyone!")
        print(request)
        print(unparsed)


def setup(bot):
    bot.add_cog(Scoring(bot))
