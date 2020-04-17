# Importing the required libraries
import datetime
import os
import requests
import time
import discord
from discord.ext import commands
import json


# DOTA2 Constants
HEROES = (requests.get("https://api.opendota.com/api/constants/heroes")).json()

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


# Defining a function to quickly calculate the average of a list
def average(list):
    return sum(list) / len(list)


# Retrieves a match, whether it's cached or not
def get_match(match_id):
    if os.path.isfile(f"resources/cached_matches/{match_id}.json"):
        with open(f"resources/cached_matches/{match_id}.json", 'r') as f:
            return json.load(f)
    else:
        matchdata = requests.get(
            f'https://api.opendota.com/api/matches/{match_id}').json()

        while matchdata == {'error': 'rate limit exceeded'}:
            print('The rate limit was passed')
            time.sleep(5)
            matchdata = (requests.get(
                f"https://api.opendota.com/api/matches/{match_id}")).json()
        if is_parsed(matchdata):
            with open(f"resources/cached_matches/{match_id}.json", 'w') as jsonFile:
                json.dump(matchdata, jsonFile)
        return matchdata


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

# Returns the benc


def average_benchmarks_single_match(player):
    bench_list = []
    for i in player['benchmarks'].values():
        bench_list.append(i['pct'])
    return round(average(bench_list) * 100, 2)


# Returns a list of the average scores over the last 50 games
def scorecalc(steamid, game_requests=50):
    recent = []
    amount_of_games = game_requests

    # Start of the main loop
    with open("resources/json_files/tracked_matches.json", 'r') as f:
        tracked_matches = json.load(f)

    if len(tracked_matches[str(steamid)]) < amount_of_games:
        amount_of_games = len(tracked_matches[str(steamid)])

    for a in range(amount_of_games):
        with open(f"resources/cached_matches/{tracked_matches[str(steamid)][a]}.json", 'r') as f:
            generaldata = json.load(f)
        matchdata = generaldata['players']

        # Gets the data of the requested user
        player = next((p for p in matchdata if str(
            p['account_id']) == steamid), None)

        # Calculating the score and appending it to a list
        # Currently does work, thanks to Sebastiaan
        recent.append(average_benchmarks_single_match(player))

    return recent


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
        rank_color = ""

        for key in rankings:  # calculating the rank
            if rankings[key]['Demotion upon'] < average_score < rankings[key]['Promotion upon']:
                obtained_rank = key
                rank_color = int(rankings[key]['color'])
                break

        rank_prefix = "an" if obtained_rank[0] in "aeiouAEIOU" else "a"
        playstyle_indication = (
            f">>> With a Score of **{average_score} %**, you played like {rank_prefix} **{obtained_rank}**")

        # the actual embed
        embed = discord.Embed(description=intro, color=rank_color,
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
            f"https://api.opendota.com/api/players/{steamid}/matches/?significant=0&limit=1&offset={skip}")).json()
        lastmatch_id = lastmatch[0]['match_id']

        await self.match(ctx, lastmatch_id, user=user)

    @commands.command()
    async def score(self, ctx, user=None, game_requests=50):
        """
        Get a player's current rank and average score.
        Supports up to 50 games.
        """
        if game_requests > 50:
            await ctx.send("This command only supports up to 50 games.\nPlease request a valid amount.")
            return
        if user is None:  # get author of message
            user = ctx.message.author.mention
        try:
            steamid = usermapping[f'{user}']
        except KeyError:
            await ctx.send("User isn't registered.")
            return
        recent = scorecalc(steamid)
        average_score = round(average(recent), 2)
        obtained_rank = ""
        rank_color = ""

        for key in rankings:  # calculating the rank
            if rankings[key]['Demotion upon'] < average_score < rankings[key]['Promotion upon']:
                obtained_rank = key
                rank_color = int(rankings[key]['color'])
                break
        rank_prefix = "an" if obtained_rank[0] in 'aeiouAEIOU' else "a"
        dota_icon = ("https://gamepedia.cursecdn.com/dota2_gamepedia/8/8b/"
                     "Main_Page_icon_Placeholder.png?version=74a035f90c52284616718c3a072c975c")
        # need this to be able to acces the personaname
        with open('resources/json_files/tracked_matches.json', 'r') as f:
            tracked_matches = json.load(f)
        # I get a random match from the user and extract the personaname from it.
        # Might be a better way to do this
        random_game = get_match(tracked_matches[steamid][0])
        player_name = next((p['personaname'] for p in random_game['players'] if str(
            p['account_id']) == steamid), None)
        intro = f"Currently is {rank_prefix} **{obtained_rank}** with an Average Score of **{average_score}**"

        embed = discord.Embed(description=intro, color=rank_color)
        embed.set_author(name=player_name or "Anonymous", icon_url=dota_icon,
                         url=f"https://www.opendota.com/players/{steamid}")
        if len(recent) < game_requests:
            note = (f">>> This score is based on only {len(recent)} games out of the requested {game_requests}.\n"
                    f"No more valid games could be found.")
            embed.add_field(name="**Not Enough Games**",
                            value=note, inline=False)
        if game_requests != 50:
            message = (
                f">>> This is not the actual score of the player,\nas normally a total of 50 games are taken into consideration.")
            embed.add_field(name="**Custom Score**",
                            value=message, inline=False)
        embed.set_footer(text=steamid)

        # adding a thumbnail with the corresponding rank icon
        rank_icon = f"{obtained_rank.lower()}.png"
        embed.set_thumbnail(url=f"attachment://{rank_icon}")
        icon = discord.File(f"resources/ranks_images/{rank_icon}", rank_icon)

        await ctx.send(embed=embed, file=icon)

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
    async def cache(self, ctx, limit=50):

        # Gets the tracked_matches dictionary or makes an empty one if it doesn't exist
        if os.path.isfile(f"resources/json_files/tracked_matches.json"):
            with open('resources/json_files/tracked_matches.json', 'r') as f:
                tracked_matches = json.load(f)
        else:
            tracked_matches = {}

        # Removes duplicates from the list
        steam_ids = list(set(usermapping.values()))

        # Main loop that iterates over all mapped steam id's
        for steamid in steam_ids:
            # Resets the cached variable
            cached = 0

            # Gets the tracked matches for a particular steam id
            if steamid in tracked_matches.keys():
                match_list = tracked_matches[steamid]
            else:
                match_list = []

            # Gets the LIMIT most recent games with offset OFFSET
            matches = (requests.get(
                f"https://api.opendota.com/api/players/{steamid}/matches/")).json()

            # Rate limit error handling
            while matches == {'error': 'rate limit exceeded'}:
                print('The rate limit was passed')
                time.sleep(5)
                matches = (requests.get(
                    f"https://api.opendota.com/api/players/{steamid}/matches/")).json()

            # Iterates over all the matches retrieved in the previous bit
            for i in range(len(matches)):
                # Resets the abandon check
                abandon = False

                # Checks if the match is stored and whether or not it's balanced
                if not os.path.isfile(f"resources/cached_matches/{matches[i]['match_id']}.json"):

                    # Gets specific match data
                    matchdata = (requests.get(
                        f"https://api.opendota.com/api/matches/{matches[i]['match_id']}")).json()

                    # Rate limit error handling
                    while matchdata == {'error': 'rate limit exceeded'}:
                        print('The rate limit was passed')
                        time.sleep(5)
                        matchdata = (requests.get(
                            f"https://api.opendota.com/api/matches/{matches[i]['match_id']}")).json()

                    # Checks if the match is parsed
                    if not is_parsed(matchdata):
                        # Checks if an unparsed match is older than a week
                        if (time.time() - matchdata['start_time']) < 604800:
                            # Sends a parse request
                            await send_parse_request(matches[i]['match_id'])
                            print(
                                f"A parse request for match {matches[i]['match_id']} was made")
                    else:
                        # Checks for any abandons
                        for p in matchdata['players']:
                            if p['leaver_status'] >= 2:
                                abandon = True
                                break

                        if abandon != True:
                            # Saves the match id to the tracked match list of this steam id
                            match_list.append(matches[i]['match_id'])
                            cached += 1

                            # Saves the match as a JSON
                            with open(f"resources/cached_matches/{matches[i]['match_id']}.json", 'w') as jsonFile:
                                json.dump(matchdata, jsonFile)

                            if cached >= limit:
                                break
                else:
                    # Saves the match id to the tracked match list of this steam id
                    match_list.append(matches[i]['match_id'])
                    cached += 1
                    if cached >= limit:
                        break

            # Trims the match_list to 50 elements
            if len(list(set(match_list))) > limit:
                match_list = sorted(set(match_list), reverse=True)[:limit]
            else:
                match_list = sorted(set(match_list), reverse=True)

            # Overwrites the previous tracked matches list
            tracked_matches[steamid] = match_list
            print(f"Done with {steamid}")

        # Writes the tracked matches dictionary to the JSON
        with open(f"resources/json_files/tracked_matches.json", 'w') as jsonFile:
            json.dump(tracked_matches, jsonFile)

        saved_matches = []
        for steamid in steam_ids:
            for i in range(len(tracked_matches[steamid])):
                saved_matches.append(f"{tracked_matches[steamid][i]}.json")

        delete = list((set(os.listdir("resources/cached_matches")
                           ) - {".gitkeep"}) - set(saved_matches))

        for d in delete:
            os.remove("resources/cached_matches/" + d)
            print(f"Deleted {d}")

        print("Done with everyone!")


def setup(bot):
    bot.add_cog(Scoring(bot))
