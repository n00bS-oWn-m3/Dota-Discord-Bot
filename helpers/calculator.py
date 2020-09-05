import json
from helpers.constants import settings, rankings
# All helper-commands related to calculating stuff

# Defining a function to quickly calculate the average of a list
def average(list):
    return sum(list) / len(list)


# return avg score of a player
def average_benchmarks_single_match(player):
    bench_list = []
    for i in player['benchmarks'].values():
        bench_list.append(i['pct'])
    return round(average(bench_list) * 100, 2)


# Returns a list of the average scores over the last X games
def scorecalc(steamid, game_requests=settings['score_games']):
    recent = []

    # Start of the main loop
    with open("resources/json_files/tracked_matches.json", 'r') as f:
        tracked_matches = json.load(f)

    if len(tracked_matches[str(steamid)]) < game_requests:
        game_requests = len(tracked_matches[str(steamid)])

    for a in range(game_requests):
        with open(f"resources/cached_matches/{tracked_matches[str(steamid)][a]}.json", 'r') as f:
            generaldata = json.load(f)
        matchdata = generaldata['players']

        # Gets the data of the requested user
        player = next((p for p in matchdata if str(
            p['account_id']) == steamid), None)

        # Calculating the score and appending it to a list
        recent.append(average_benchmarks_single_match(player))

    return recent


# calculate the rank, based on an average score:
def get_rank(average_score):
    for key in rankings:  # calculating the rank
        if rankings[key]['Demotion upon'] < average_score < rankings[key]['Promotion upon']:
            return key