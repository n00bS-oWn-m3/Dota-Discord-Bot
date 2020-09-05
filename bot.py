from discord.ext import commands
import json
import os


# Loads the bot token from a json file that contains it as a string
with open('resources/json_files/settings.json', 'r') as f:
        settings = json.load(f)

def get_prefix(client, message):
    if os.path.isfile('resources/json_files/prefixes.json'):
        with open('resources/json_files/prefixes.json', 'r') as f:
            prefixes = json.load(f)

        if not message.guild.id in prefixes:
            prefixes[str(message.guild.id)] = settings['default_prefix']
            
            with open('resources/json_files/prefixes.json', 'w') as f:
                json.dump(prefixes, f)
    else:
        prefixes = {str(message.guild.id): "."}
        with open('resources/json_files/prefixes.json', 'w') as f:
            json.dump(prefixes, f)

    return prefixes[str(message.guild.id)]

bot = commands.Bot(command_prefix=get_prefix)

@bot.event
async def on_ready():
    print(f'Ping: {round(bot.latency * 1000)} ms\nBot is ready.')

# makes sure commands only work in a guild
@bot.check
async def globbaly_block_dm(ctx):
    return ctx.guild is not None

# load, unload and reload help to enable and disable cogs
@bot.command()
@commands.has_role('Dev')
async def load(ctx, extension):
    """Load a specific cog"""
    bot.load_extension(f'cogs.{extension}')
    await ctx.message.add_reaction("✅")

@bot.command()
@commands.has_role('Dev')
async def unload(ctx, extension):
    """Unload a specific cog"""
    bot.unload_extension(f'cogs.{extension}')
    await ctx.message.add_reaction("✅")

@bot.command()
@commands.has_role('Dev')
async def reload(ctx, extension): # bcs I'm lazy
    """Unloads and loads a specific cog"""
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')
    await ctx.message.add_reaction("✅")


# load all .py files (without '.py') from ./cogs
for f in os.listdir('./cogs'):
    if f.endswith('.py'):
        bot.load_extension(f'cogs.{f[:-3]}')

# we don't want to display the example cog
bot.unload_extension('cogs.example')
bot.run(settings['token'])