import discord
from discord.ext import commands
import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG)

AUTHORIZED_ROLE_ID = 1256966092618989681
AUTHORIZED_CHANNEL_ID = 1256736760424300654
SIZE_CHANNEL_ID = 1257298275149549689
MESSAGE_ID_TO_KEEP = 1256977850452541571

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def is_in_authorized_channel(ctx):
    if ctx.channel.id != AUTHORIZED_CHANNEL_ID:
        authorized_channel = bot.get_channel(AUTHORIZED_CHANNEL_ID)
        await ctx.reply(f"Please use the commands in {authorized_channel.mention}.")
        return False
    return True

async def check_size_channel(ctx):
    if ctx.channel.id != SIZE_CHANNEL_ID:
        size_channel = bot.get_channel(SIZE_CHANNEL_ID)
        await ctx.reply(f"Please use the commands in {size_channel.mention}.")
        return False
    return True

def has_authorized_role(ctx):
    role = discord.utils.get(ctx.guild.roles, id=AUTHORIZED_ROLE_ID)
    return role in ctx.author.roles

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
@commands.check(is_in_authorized_channel)
async def add(ctx, *, name: str):
    """Adds a vote for the given name."""
    user_id = str(ctx.author.id)
    conn = sqlite3.connect('votes.db')
    c = conn.cursor()

    c.execute("SELECT * FROM user_votes WHERE user_id=? AND name=?", (user_id, name))
    if c.fetchone():
        await ctx.reply("You have already voted for this name.")
    else:
        c.execute("INSERT OR IGNORE INTO votes (name, vote_count) VALUES (?, 0)", (name,))
        c.execute("UPDATE votes SET vote_count = vote_count + 1 WHERE name=?", (name,))
        c.execute("INSERT INTO user_votes (user_id, name) VALUES (?, ?)", (user_id, name))
        conn.commit()
        await ctx.reply(f"Your vote for **{name}** has been recorded.")

    conn.close()

@bot.command()
@commands.check(is_in_authorized_channel)
async def top(ctx):
    """Shows the top 10 most voted names."""
    conn = sqlite3.connect('votes.db')
    c = conn.cursor()

    c.execute("SELECT name, vote_count FROM votes ORDER BY vote_count DESC LIMIT 10")
    top_names = c.fetchall()

    if top_names:
        response = "Top 10 most wanted:\n"
        for idx, (name, vote_count) in enumerate(top_names, start=1):
            response += f"> **{idx}**. @{name} - **{vote_count}** votes\n"
    else:
        response = "No votes at the moment."

    await ctx.send(response)
    conn.close()

@bot.command()
@commands.check(is_in_authorized_channel)
async def find(ctx, *, name: str):
    """Finds the number of votes for the given name."""
    conn = sqlite3.connect('votes.db')
    c = conn.cursor()

    c.execute("SELECT vote_count FROM votes WHERE name=?", (name,))
    result = c.fetchone()

    if result:
        vote_count = result[0]
        response = f"{name} is wanted with **{vote_count}** votes."
    else:
        response = f"{name} is not wanted for now."

    await ctx.reply(response)
    conn.close()

@bot.command()
@commands.check(is_in_authorized_channel)
async def set(ctx, name: str, vote_count: int):
    """Sets the vote count for the given name (authorized role only)."""
    if not has_authorized_role(ctx):
        await ctx.reply("You are not authorized to use this command.")
        return

    conn = sqlite3.connect('votes.db')
    c = conn.cursor()

    c.execute("INSERT OR REPLACE INTO votes (name, vote_count) VALUES (?, ?)", (name, vote_count))
    conn.commit()

    await ctx.reply(f"The vote count for **{name}** has been set to **{vote_count}**.")
    conn.close()

@bot.command(name="del")
async def del_user(ctx, *, name: str):
    """Deletes the given name and its votes or size (authorized role only)."""
    if not has_authorized_role(ctx):
        await ctx.reply("You are not authorized to use this command.")
        return

    if ctx.channel.id == AUTHORIZED_CHANNEL_ID:
        conn = sqlite3.connect('votes.db')
        c = conn.cursor()

        c.execute("DELETE FROM votes WHERE name=?", (name,))
        c.execute("DELETE FROM user_votes WHERE name=?", (name,))
        conn.commit()

        if c.rowcount > 0:
            response = f"The name {name} and its votes have been deleted."
        else:
            response = f"The name {name} was not found."

    elif ctx.channel.id == SIZE_CHANNEL_ID:
        conn = sqlite3.connect('sizes.db')
        c = conn.cursor()

        c.execute("DELETE FROM sizes WHERE name=?", (name,))
        conn.commit()

        if c.rowcount > 0:
            response = f"The name {name} and its size have been deleted."
        else:
            response = f"The name {name} was not found."

    await ctx.reply(response)
    conn.close()

@bot.command()
@commands.check(is_in_authorized_channel)
async def clear(ctx, amount: int = 10):
    """Clears the last 10 messages in the channel (authorized role only)."""
    if not has_authorized_role(ctx):
        await ctx.reply("You are not authorized to use this command.")
        return

    deleted = 0
    async for message in ctx.channel.history(limit=amount):
        if message.id != MESSAGE_ID_TO_KEEP:
            await message.delete()
            deleted += 1

    await ctx.send(f"Cleared {deleted} messages.", delete_after=5)

@bot.command()
@commands.check(check_size_channel)
async def size(ctx, name: str, size: int):
    """Sets the size for the given name (authorized role only)."""
    if not has_authorized_role(ctx):
        await ctx.reply("You are not authorized to use this command.")
        return

    conn = sqlite3.connect('sizes.db')
    c = conn.cursor()

    c.execute("INSERT OR REPLACE INTO sizes (name, size) VALUES (?, ?)", (name, size))
    conn.commit()

    await ctx.reply(f"The size for **{name}** has been set to **{size:,}**.")
    conn.close()

@bot.command()
@commands.check(check_size_channel)
async def big(ctx):
    """Shows the top 100 names with the highest size."""
    conn = sqlite3.connect('sizes.db')
    c = conn.cursor()

    c.execute("SELECT name, size FROM sizes ORDER BY size DESC LIMIT 100")
    top_sizes = c.fetchall()

    if top_sizes:
        response = "Top 100 sizes:\n"
        for idx, (name, size) in enumerate(top_sizes, start=1):
            response += f"> **{idx}**. @{name} - **{size:,}**\n"
    else:
        response = "No sizes at the moment."

    await ctx.reply(response)
    conn.close()

bot.run('Secret')
