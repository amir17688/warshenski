#!/usr/bin/env python3

# Vishnu by Valkyrie
#
# Discord bot that handles dice rolling and other things

import discord, yaml, vroll, pgsql, re
import texttable as tt
from discord.ext import commands

config = yaml.safe_load(open("config.yaml"))
token = config['token']
chan_whitelist = config['chan_whitelist']
pg_connection = config['pg_connection']
role_whitelist = config['role_whitelist']
permission_error_message = config['permission_error_message']
quest_tier_whitelist = config['quest_tiers']

# Create PostgreSQL tables.
pgsql.create_tables(pg_connection)

description = """
Vishnu, a multipurpose D&D bot.
"""

bot = commands.Bot(command_prefix='!', description=description)

"""
Role whitelisting function
"""
def whitelist_check(ctx):
    for x in role_whitelist:
        if x in [y.id for y in ctx.message.author.roles]:
            return True
        else:
            return False

"""
QUEST-RELATED COMMANDS
"""
@bot.command()
async def addquest(ctx, quest_tier, *desc):
    """
    Allows a DM to create a quest.

    !addquest [TIER] [DESCRIPTION]
    """

    if whitelist_check(ctx):
        if quest_tier in quest_tier_whitelist:
            if len(desc) < 100:
                quest_desc = " ".join(desc)
                creator = str(ctx.author)

                pgsql.import_quest_data(pg_connection, quest_tier, quest_desc, creator)

                print("Tier {} quest added by {}. Description: {}".format(quest_tier, str(ctx.author), quest_desc))
                await ctx.send("Tier {} quest added by {}. Description: {}".format(quest_tier, str(ctx.author), quest_desc))
            else:
                await ctx.send("Error: Your description is too long. The maximum allowed characters is 100, you had " + str(len(desc)))
        else:
            await ctx.send("Error: The quest tier you specified is invalid. The valid quest tiers are: " + ", ".join(quest_tier_whitelist) + ". You specified: " + quest_tier)
    else:
        await ctx.send(permission_error_message)

@bot.command()
async def delquest(ctx, quest_id):
    """
    Allows a DM to delete a quest by their ID.

    !delquest [ID]
    """

    if whitelist_check(ctx):
        pgsql.delete_quest(pg_connection, quest_id)
        await ctx.send("Quest with ID " + quest_id + " deleted.")
    else:
        await ctx.send(permission_error_message)

@bot.command()
async def questcomplete(ctx, quest_id):
    """
    Allows a DM to set a quest to 'complete' by specifying a quest ID.

    !questcomplete [ID]
    """

    if whitelist_check(ctx):
        pgsql.complete_quest(pg_connection, quest_id, True)
    else:
        await ctx.send(permission_error_message)

@bot.command()
async def questuncomplete(ctx, quest_id):
    """
    Allows a DM to set a quest to 'uncomplete' by specifying a quest ID.

    !questuncomplete [ID]
    """

    if whitelist_check(ctx):
        pgsql.complete_quest(pg_connection, quest_id, False)
    else:
        await ctx.send("You don't have permission to use this command")

@bot.command()
async def getquest(ctx, *args):
    """
    Allows any user to retrieve quests by specifying an ID, tier, or creator. Otherwise, returns all quests.

    !getquest [id=ID] [tier=TIER] [creator=CREATOR]
    """

    command = " ".join(map(str, args))

    idsearch= "id=([\d])"
    tiersearch= "tier=([^\s]+)"
    creatorsearch= "creator=([^\s]+)"
    idformat = ""
    tierformat= ""
    creatorformat= ""

    if re.search(idsearch, command) is not None:
        idmatch = re.search(idsearch, command).group(1)
        idformat = "AND id = {}".format(idmatch)

    if re.search(tiersearch, command) is not None:
        tiermatch = re.search(tiersearch, command).group(1)
        tierformat = "AND tier = '{}'".format(tiermatch)
    if re.search(creatorsearch, command) is not None:
        creatormatch = re.search(creatorsearch, command).group(1)
        creatorformat = "AND creator = '{}'".format(creatormatch)

    # Craft a postgres SQL query.
    query = """
    SELECT id, tier, creator, description FROM quests
    WHERE completed = 'f'
    {}
    {}
    {};
    """.format(idformat, tierformat, creatorformat)

    query_return = pgsql.retrieve_quest_data(pg_connection, query) # Execute our query

    # Format the results as a table
    tab = tt.Texttable()
    headings = ['ID', 'TIER', 'CREATOR', 'DESCRIPTION']
    tab.header(headings)

    for x in range(0, len(query_return), 5):
        for row in query_return[x:x+5]:
            tab.add_row(row)


        s = tab.draw()
        print(len(query_return))
        await ctx.send("```" + s + "```")
        tab.reset()

"""
DICE COMMANDS
"""
@bot.command()
async def roll(ctx, *args):
    """
    Rolls dice.

    !roll [NUM]d[FACES]+[NUM]
    """

    if chan_whitelist is None: # If the whitelist is empy, run the roll function in any channel
        for x in args:
            print("!roll command recieved in channel ID " + str(ctx.channel.id))
            await ctx.send(vroll.roll(x))


    elif ctx.channel.id in chan_whitelist: # Checks for the channel ID in the whitelist
        for x in args:
            print("!roll command recieved in channel ID " + str(ctx.channel.id) + " by user " + str(ctx.author))
            await ctx.send(vroll.roll(x))

@bot.event
async def on_ready():
    print("{0.user} connected to server".format(bot))
    print("Whitelisted channel IDs are: " + str(chan_whitelist))
    print("Whitelisted role IDs are: " + str(role_whitelist))

bot.run(token)
