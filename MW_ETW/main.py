import discord
from discord.ext import commands
import sqlite3
import logging

# Configurer le logging
logging.basicConfig(level=logging.DEBUG)

AUTHORIZED_USER_ID = 278955863115431975

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')

@bot.event
async def on_connect():
    print("Bot has connected to Discord")

@bot.event
async def on_disconnect():
    print("Bot has disconnected from Discord")

@bot.command()
async def add(ctx, *, name: str):
    """Adds a vote for the given name."""
    user_id = str(ctx.author.id)
    conn = sqlite3.connect('votes.db')
    c = conn.cursor()

    # Vérifier si l'utilisateur a déjà voté pour ce nom
    c.execute("SELECT * FROM user_votes WHERE user_id=? AND name=?", (user_id, name))
    if c.fetchone():
        await ctx.send("You have already voted for this name.")
    else:
        # Ajouter le nom ou incrémenter les votes
        c.execute("INSERT OR IGNORE INTO votes (name, vote_count) VALUES (?, 0)", (name,))
        c.execute("UPDATE votes SET vote_count = vote_count + 1 WHERE name=?", (name,))
        # Enregistrer le vote de l'utilisateur
        c.execute("INSERT INTO user_votes (user_id, name) VALUES (?, ?)", (user_id, name))
        conn.commit()
        await ctx.send(f"Your vote for {name} has been recorded.")

    conn.close()

@bot.command()
async def top(ctx):
    """Shows the top 10 most voted names."""
    conn = sqlite3.connect('votes.db')
    c = conn.cursor()

    # Récupérer les 10 noms les plus votés
    c.execute("SELECT name, vote_count FROM votes ORDER BY vote_count DESC LIMIT 10")
    top_names = c.fetchall()

    if top_names:
        response = "Top 10 most voted names:\n"
        for idx, (name, vote_count) in enumerate(top_names, start=1):
            response += f"{idx}. {name} - {vote_count} votes\n"
    else:
        response = "No votes at the moment."

    await ctx.send(response)
    conn.close()

@bot.command()
async def find(ctx, *, name: str):
    """Finds the number of votes for the given name."""
    conn = sqlite3.connect('votes.db')
    c = conn.cursor()

    # Chercher le nom dans la base de données
    c.execute("SELECT vote_count FROM votes WHERE name=?", (name,))
    result = c.fetchone()

    if result:
        vote_count = result[0]
        response = f"{name} is wanted with {vote_count} votes."
    else:
        response = f"{name} is not wanted for now."

    await ctx.send(response)
    conn.close()

@bot.command()
async def del_user(ctx, *, name: str):
    """Deletes the given name and its votes (authorized user only)."""
    if ctx.author.id != AUTHORIZED_USER_ID:
        await ctx.send("You are not authorized to use this command.")
        return

    conn = sqlite3.connect('votes.db')
    c = conn.cursor()

    # Supprimer le nom et ses votes
    c.execute("DELETE FROM votes WHERE name=?", (name,))
    c.execute("DELETE FROM user_votes WHERE name=?", (name,))
    conn.commit()

    if c.rowcount > 0:
        response = f"The name {name} and its votes have been deleted."
    else:
        response = f"The name {name} was not found."

    await ctx.send(response)
    conn.close()

# Remplace 'YOUR_TOKEN' par le token de votre bot
bot.run('')
