from discord.ext import commands
import json
import os



def get_prefix(client, message):
    with open('resources/json_files/prefixes.json', 'r') as f:
        prefixes = json.load(f)

    return prefixes[str(message.guild.id)]

bot = commands.Bot(command_prefix=get_prefix)

@bot.event
async def on_ready():
    print(f'Ping: {round(bot.latency * 1000)} ms\nBot is ready.')


# load, unload and reload help to enable and disable cogs
@bot.command()
@commands.has_role('Dev')
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')

@bot.command()
@commands.has_role('Dev')
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')

@bot.command()
@commands.has_role('Dev')
async def reload(ctx, extension): # bcs I'm lazy
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')


# load all .py files (without '.py') from ./cogs
for f in os.listdir('./cogs'):
    if f.endswith('.py'):
        bot.load_extension(f'cogs.{f[:-3]}')

# we don't want to display the example cog
bot.unload_extension('cogs.example')

bot.run('REDACTED')
