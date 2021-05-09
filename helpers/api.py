import asyncio
import os
import json
import aiohttp
import requests
# All helper-commands related to communicating with the OpenDota API

# Make an API-request and return it as dictionary
async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()


# check if a game is already parsed
def is_parsed(match):
    return match.get('version', None) is not None


# Retrieves a match, whether it's cached or not
async def get_match(match_id):
    if os.path.isfile(f"resources/cached_matches/{match_id}.json"):
        with open(f"resources/cached_matches/{match_id}.json", 'r') as f:
            return json.load(f)
    else:
        async with aiohttp.ClientSession() as session:
            matchdata = await fetch(session, f'https://api.opendota.com/api/matches/{match_id}')

            while matchdata == {'error': 'rate limit exceeded'}:
                print('The rate limit was passed')
                await asyncio.sleep(5)
                matchdata = await fetch(session, f'https://api.opendota.com/api/matches/{match_id}')
        if is_parsed(matchdata):
            with open(f"resources/cached_matches/{match_id}.json", 'w') as jsonFile:
                json.dump(matchdata, jsonFile)
        return matchdata


# request a parse by specific match-id
def send_parse_request(match_id):
    requests.post(f'https://api.opendota.com/api/request/{match_id}')

