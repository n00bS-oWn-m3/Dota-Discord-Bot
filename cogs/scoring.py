# Importing the required libraries
import datetime

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

# All ranks with extra information
with open('resources/json_files/rankings.json', 'r') as f:
    rankings = json.load(f)


# request a parse by specific match-id
async def send_parse_request(match_id):
    requests.post(f'https://api.opendota.com/api/request/{match_id}')

# check if a game is already parsed
def is_parsed(match):
    return match.get('version', None) is not None

#convert the time in seconds to a nice string (up to hours, since I don't reckon any dota game will be any longer)
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
    if len(result) == 3: # up to hours
        return f"{result[0]}, {result[1]} and {result[2]}"
    elif len(result) == 2: # up to minutes
        return f"{result[0]} and {result[1]}"
    elif len(result) == 1: # up to seconds
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
        while len(self.recent) < self.game_requests:

            self.workable = True

            # Gets the most recent all draft match in a standard lobby for the given account_id that hasn't been processed yet
            self.match = (requests.get(
                f"https://api.opendota.com/api/players/{self.account_id}/matches/?limit=1&game_mode=22&lobby_type=0&offset={self.attempts}")).json()

            # Checking to see if we've passed the rate limit
            while self.match == {'error': 'rate limit exceeded'}:
                print('The rate limit was passed')
                time.sleep(5)
                self.match = (requests.get(
                    f"https://api.opendota.com/api/players/{self.account_id}/matches/?limit=1&game_mode=22&lobby_type=0&offset={self.attempts}")).json()
            else: # What's the else for?
                if self.match == []:   
                    break    
                else:
                    # Increments the attempts variable by one, it's used to always go back one game
                    self.attempts = self.attempts + 1

                    # Extracts the match_id and player slot from the X'th most recent game
                    self.match_id = self.match[0]['match_id']
                    self.player_slot = self.match[0]['player_slot']

                    if self.player_slot >= 128:
                        self.player_slot -= 123

                    # Retrieves the data for the given match_id
                    self.generaldata = (requests.get(
                        f"https://api.opendota.com/api/matches/{self.match_id}")).json()
                    self.matchdata = self.generaldata['players']

                    # Retrieves the data for the given player_slot
                    self.player = self.matchdata[self.player_slot]

                    # Checking to see if the match has been parsed and any abandons have been registered
                    # I feel like there's a better way to go about this, but for now it'll do just fine
                    if not is_parsed(self.generaldata):
                        if (time.time() - self.match[0]['start_time']) < 1209600:
                            # Posts a parse request to the opendota servers
                            requests.post(f'https://api.opendota.com/api/request/{self.match_id}')

                            # Increments the unparsed_matches variable by 1
                            self.unparsed_matches += 1

                            # Alerts the user of the unparsed state of the match
                            if self.debug >= 2:
                                print(
                                    f"Match {self.match_id} has not been parsed yet, a request has been sent to the servers.")
                                print()

                            # Marks the match as unworkable
                            self.workable = False
                        
                        else:
                            # Increments the unparsed_old_matches variable by 1
                            self.unparsed_old_matches += 1
                            
                            # Alerts the user of the unparseable state of the match
                            if self.debug >= 2:
                                print(
                                    f"Match {self.match_id} is no longer parseable due to it being older than two weeks.\n")

                            # Marks the match as unworkable
                            self.workable = False

                    # Checks if any players have abandoned the game
                    else:
                        for self.player_slot in range(10):
                            if self.matchdata[self.player_slot]['leaver_status'] >= 2:
                                self.abandons += 1
                                self.workable = False
                                break

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
                    print(f"Player slot: {self.player_slot}")
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
        match = requests.get(f'https://api.opendota.com/api/matches/{match_id}').json()
        if match == {"error": "Not Found"}:
            await ctx.send("Please use a valid match-id.")
        if not is_parsed(match):
            await ctx.send("Match isn't parsed yet. Please retry in a few moments.")
            await ctx.send("⏳ Requesting a parse...", delete_after=5)
            await send_parse_request(match_id)
        if user is None: # get author of message
            user = ctx.message.author.mention
        try:
            steamid = usermapping[f'{user}']
        except KeyError:
            await ctx.send("User isn't registered.")
            return
        player = next((p for p in match['players'] if str(p['account_id']) == steamid), None)
        if player is None: # didn't find any matching account_id
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

        for key in rankings: # calculating the rank
            if rankings[key]['Demotion upon'] < average_score < rankings[key]['Promotion upon']:
                obtained_rank = key
                break

        rank_prefix = "an" if obtained_rank[0] in "aeiouAEIOU" else "a"
        playstyle_indication=(f">>> With a Score of **{average_score} %**, you played like {rank_prefix} **{obtained_rank}**")


        # the actual embed
        embed = discord.Embed(description=intro, color=297029, timestamp=datetime.datetime.utcfromtimestamp(match['start_time']))
        embed.set_author(name=player['personaname'] or "Anonymous", icon_url=hero_icon, url=f"https://www.opendota.com/players/{steamid}")
        bm = player['benchmarks']

        # adding warning message, if necessary
        if warning_necessary:
            embed.add_field(name="**Warning**", value=warning_notice, inline=False)

        # adding the playstyle-indication
        embed.add_field(name=obtained_rank + " Player", value=playstyle_indication, inline=False)

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
        if user is None: # get author of message
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
    async def score(self, ctx, user=None, game_requests=5, debug=0):
        
        if user is None:
                await ctx.send('Enter a name, and optionally an amount of games to process')
        
        elif user not in usermapping.keys():
            await ctx.send("That user isn't registered.")
        
        else: 
            score = Scorecalc(f'{user}', game_requests, debug)

            score.calculate()

            await ctx.send(f"Average over {len(score.recent)} games: {round(average(score.recent),3)}")

            if len(score.recent) < game_requests:
                await ctx.send(f"I could only find {len(score.recent)} valid games to process instead of the requested {game_requests}.")

            if score.unparsed_matches == 1:
                await ctx.send(f"{score.unparsed_matches} match has not been parsed yet, please try again in a few minutes for updated results.")
            elif score.unparsed_matches > 1:
                 await ctx.send(f"{score.unparsed_matches} matches have not been parsed yet, please try again in a few minutes for updated results.")
           
            if score.debug >= 1:
                if score.abandons == 1:
                    await ctx.send(f"{score.abandons} match was abandoned by someone, it was not taken into consideration.")
                elif score.abandons > 1:
                    await ctx.send(f"{score.abandons} matches were abandoned by someone, they were not taken into consideration.")
                
                if score.unparsed_old_matches == 1:
                    await ctx.send(f"{score.unparsed_old_matches} unparsed match is older than two weeks and can't be parsed anymore.")
                elif score.unparsed_old_matches > 1:
                    await ctx.send(f"{score.unparsed_old_matches} unparsed matches are older than two weeks and can't be parsed anymore.")

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


def setup(bot):
    bot.add_cog(Scoring(bot))