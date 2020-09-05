from helpers.json import get_json
import requests
# Just a bunch of constants

HEROES = (requests.get("https://api.opendota.com/api/constants/heroes")).json() # DOTA2 constants
settings = get_json('settings.json')  # bot settings (to personalize commands)
game_modes = get_json('game_mode.json')  # all game modes
lobby_types = get_json('lobby_type.json')  # all lobby types
rankings = get_json('rankings.json')  # all ranks with extra information
usermapping = get_json('usermapping.json')  # information about registered users
