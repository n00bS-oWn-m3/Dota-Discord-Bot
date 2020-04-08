import discord
from discord.ext import commands
from discord.utils import get
import json

class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot



# update prefixes.json if a new server joins/leaves
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)
        prefixes[str(guild.id)] = '.'

        with open('prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)
        prefixes.pop(str(guild.id))

        with open('prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)



    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        print(f'{member} has joined the server.')
        role = get(member.guild.roles, name='Local')
        await member.add_roles(role)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        print(f'{member} has left the server.')

def setup(bot):
    bot.add_cog(Events(bot))