# Importing the required libraries
import requests
import time
import discord
from discord.ext import commands
import json


# Defining a function to quickly calculate the average of a list
def average(list):
    return sum(list) / len(list)


# A dictionary of our account ID's
with open('usermapping.json') as f: 
    usermapping = json.load(f)


# Setting up a class
# All it needs is a name from the hardcoded dictionary, amount of games to analyze and whether to print out individual match data are optional arguments
class Scorecalc:

    # DOTA2 Constants
    HEROES = (requests.get("https://api.opendota.com/api/constants/heroes")).json()

    def __init__(self, user, amount_of_games=5, print_matches=False):
        # Making empty variables and other setup
        self.recent = []
        self.benchmarks = []
        self.unparsed_matches = 0
        self.abandons = 0
        self.attempts = 0

        self.account_id = usermapping[f'{user}']
        self.amount_of_games = amount_of_games
        self.print_matches = print_matches

    def calculate(self):
        # Start of the main loop
        while len(self.recent) < self.amount_of_games:

            self.workable = True

            # Gets the most recent all draft match in a standard lobby for the given account_id that hasn't been processed yet
            self.match = (requests.get(
                f"https://api.opendota.com/api/players/{self.account_id}/matches/?limit=1&game_mode=22&lobby_type=0&offset={self.attempts}")).json()

            # Checking to see if we've passed the rate limit
            if self.match == {'error': 'rate limit exceeded'}:
                time.sleep(5)
                self.match = (requests.get(
                    f"https://api.opendota.com/api/players/{self.account_id}/matches/?limit=1&game_mode=22&lobby_type=0&offset={self.attempts}")).json()

            else:
                # Increments the attempts variable by one, it's used to always go back one game
                self.attempts = self.attempts + 1

                # Extracts the match_id and player slot from the X'th most recent game
                self.match_id = self.match[0]['match_id']
                self.player_slot = self.match[0]['player_slot']

                if self.player_slot >= 128:
                    self.player_slot = self.player_slot - 123

                # Retrieves the data for the given match_id
                self.data = (requests.get(
                    f"https://api.opendota.com/api/matches/{self.match_id}")).json()['players']

                # Retrieves the data for the given player_slot
                self.player = self.data[self.player_slot]

                # Checking to see if the match has been parsed and any abandons have been registered
                # I feel like there's a better way to go about this, but for now it'll do just fine
                if self.player['ability_targets'] == None:
                    # Posts a parse request to the opendota servers
                    requests.post(
                        f'https://api.opendota.com/api/request/{self.match_id}')
                    print('Requesting parse')

                    # Increments the unparsed_matches variable by 1
                    self.unparsed_matches = self.unparsed_matches + 1

                    # Alerts the user of the unparsed state of the match
                    if self.print_matches == True:
                        print(
                            f"Match {self.match_id} has not been parsed yet, a request has been sent to the servers.")
                        print()

                    # Marks the match as unworkable
                    self.workable = False

                # Checks if any players have abandoned the game
                else:
                    for self.player_slot in range(0, 10):
                        if self.data[self.player_slot]['leaver_status'] >= 2:
                            self.abandons = self.abandons + 1
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
                if self.print_matches == True:
                    print(f"Match ID: {self.match_id}")
                    print(f"Player slot: {self.player_slot}")
                    print(
                        f"Hero: {self.HEROES[f'{self.hero_id}']['localized_name']}")
                    print(
                        f"Score: {round(self.recent[len(self.recent) - 1], 3)}")
                    print()










# Setting up the Scoring cog
class Scoring(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def score(self, ctx, user=None, amount_of_games=5):
        
        if user is None:
                await ctx.send('Enter a name, and optionally an amount of games to process')
        
        elif user not in usermapping.keys():
            await ctx.send("That user isn't registered.")
        
        else: 
            score = Scorecalc(f'{user}', amount_of_games)

            score.calculate()

            await ctx.send(f"Average over {len(score.recent)} games: {round(average(score.recent),3)}")

            if score.unparsed_matches == 1:
                await ctx.send(f"{score.unparsed_matches} match has not been parsed yet, please try again in a few minutes for updated results.")
            elif score.unparsed_matches > 1:
                await ctx.send(f"{score.unparsed_matches} matches have not been parsed yet, please try again in a few minutes for updated results.")

            if score.abandons == 1:
                await ctx.send(f"{score.abandons} match was abandoned by someone, it was not taken into consideration.")
            elif score.abandons > 1:
                await ctx.send(f"{score.abandons} matches were abandoned by someone, they were not taken into consideration.")


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def register(self, ctx, user, id):
        
        if len(id) != 9 or isinstance(id, int):
            await ctx.send("Please use the last part of a valid SteamID3.")
        
        else:   
            usermap = {f'{user}': f'{id}'}    

            with open('usermapping.json') as f: 
                data = json.load(f)  
            
            data.update(usermap)

            with open('usermapping.json', 'w') as f:
                json.dump(data, f, indent=4)    


            await ctx.send(f"User {user} registered with Steam ID {id}.")


def setup(bot):
    bot.add_cog(Scoring(bot))