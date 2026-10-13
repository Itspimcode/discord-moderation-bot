import os
from http.cookiejar import cut_port_re

import discord
import sqlite3
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from  datetime import  timedelta

#sql database

db = sqlite3.connect("data_disocrd.db")
cursor = db.cursor()


#makes a tabel

cursor.execute("""
   CREATE TABLE IF NOT EXISTS warnings (
    user_id INTEGER,
    guild_id INTEGER,
    warning_count INTEGER,
    PRIMARY KEY (user_id, guild_id) 
)
""")
db.commit()



# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Setup intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:

        return

    #the bad words
    bad_words = ["fool", "testword", "shu", "bad"]

    #the bad word cheek
    if any(word in message.content.lower() for word in bad_words):
       #delete the bad msg

        try:
            await  message.delete()
        except discord.Forbidden:
          print("Bot lacks permission to delete thus message.")

            #add or upadte the users warning count

        cursor.execute(
                """
                INSERT INTO warnings (user_id, guild_id, warning_count) VALUES (?, ?, 1)
                ON CONFLICT(user_id, guild_id) 
                DO UPDATE SET warning_count = warning_count + 1
            """,
                (message.author.id, message.guild.id),
            )
        db.commit()

        cursor.execute(
           "SELECT warning_count FROM warnings WHERE user_id = ? AND guild_id = ?",
           (message.author.id, message.guild.id)

       )

        current_warnings = cursor.fetchone()[0]


        if current_warnings == 3:
            try:
                await message.author.timeout(timedelta(minutes=10), reason="3 warnings")
                await message.channel.send(
                    f"{message.author.mention} reached 3 warnings and was timed out"

                )
            except discord.Forbidden:
                print("bot lacks permission to timeout")


        elif current_warnings >= 5:
            try:
                await  message.author.ban(reason="Reached 5 warnings")
                await  message.channel.send(
                    f"{message.author.mention} was baned for reaching 5 warnings"





                )

                cursor.execute(

                    "DELETE FROM warnings WHERE user_id = ? AND guild_id = ?",

                    (message.author.id, message.guild.id)

                )

                db.commit()



            except discord.Forbidden:
                print("bot lacks permisson to bad this user")




                await message.channel.send(
                    f"{message.author.mention}, that word is not allowed!"

            )
        
    await bot.process_commands(message)




# START
#########################
#############################
###############################

@bot.tree.command(name="say", description="A say command")
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)

@bot.tree.command(name="warnings", description="Check a user's warnings")
@app_commands.describe(member="The user you want to check")
@app_commands.checks.has_permissions(manage_messages=True)
async def warnings(interaction: discord.Interaction, member: discord.Member):

    cursor.execute(
        "SELECT warning_count FROM warnings WHERE user_id = ? AND guild_id = ?",
        (member.id, interaction.guild.id)
    )
    result = cursor.fetchone()

    count = result[0] if result else 0

    await  interaction.response.send_message(f"{member.mention} has **{count}** warnings(s).")

@bot.tree.command(name="clearwarnings", description="Reset a user's warnings back to 0")
@app_commands.describe(member="The user whoes warnings you whant to clear")
@app_commands.checks.has_permissions(manage_messages=True)
async def clearwarnings(interaction: discord.Interaction, member: discord.Member):

    cursor.execute(
        "DELETE FROM warnings WHERE user_id = ? AND guild_id = ?",

        (member.id, interaction.guild.id)

    )
    db.commit()

    await  interaction.response.send_message(
        f" Cleard all warnings for {member.mention}!"

    )




bot.run(TOKEN)