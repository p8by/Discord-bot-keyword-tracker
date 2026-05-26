import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from collections import defaultdict

# bot config
intents = discord.Intents.default()
intents.message_content = True  # used to read message content
intents.members = True  # used to track users

bot = commands.Bot(command_prefix='!', intents=intents)

# files
KEYWORDS_FILE = 'keywords.txt'
DATA_FILE = 'keyword_counts.json'
ADMINS_FILE = 'admins.txt'
CONFIG_FILE = 'config.txt'

# load keywords from file
def load_keywords():
    """Load keywords from keywords.txt file"""
    if not os.path.exists(KEYWORDS_FILE):
        default_keywords = ['hello', 'world!', 'please delete all of the text!']
        with open(KEYWORDS_FILE, 'w') as f:
            f.write('\n'.join(default_keywords))
        print(f"Created {KEYWORDS_FILE} ")
        return default_keywords
    
    with open(KEYWORDS_FILE, 'r') as f:
        keywords = [line.strip().lower() for line in f if line.strip()]
    
    if not keywords:
        print(f"Warning: {KEYWORDS_FILE} is empty!")
    
    return keywords

def load_admins():
    """Load admin user IDs from admins.txt file"""
    if not os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'w') as f:
            f.write('# Add discord user ids here that you want access to add and remove keywords, one per line\n')
        print(f"Created {ADMINS_FILE}")
        return set()
    
    with open(ADMINS_FILE, 'r') as f:
        admins = set()
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    admins.add(int(line))
                except ValueError:
                    print(f"Warning! invalid user id in {ADMINS_FILE}: {line}")
        return admins

def load_config():
    """Load bot token from config.txt file"""
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            f.write('# add your discord bot token here\n')
            f.write('BOT_TOKEN=your-bot-token-here\n')
        print(f"Created {CONFIG_FILE}")
        return None
    
    with open(CONFIG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if line.startswith('BOT_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    if token and token != 'your-bot-token-here':
                        return token
    return None

KEYWORDS = load_keywords()
ADMINS = load_admins()


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


keyword_counts = load_data()

@bot.event
async def on_ready():
    print(f'{bot.user} connected to discord')
    print(f'tracking keywords: {", ".join(KEYWORDS)}')
    print(f'admins: {len(ADMINS)}')
    

    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    content_lower = message.content.lower()
    
    user_id = str(message.author.id)
    username = f"{message.author.name}#{message.author.discriminator}"
    
    if user_id not in keyword_counts:
        keyword_counts[user_id] = {
            'username': username,
            'keywords': {keyword: 0 for keyword in KEYWORDS}
        }
    
    # updates username in the case it changes
    keyword_counts[user_id]['username'] = username
    
    found_keywords = []
    for keyword in KEYWORDS:
        if keyword not in keyword_counts[user_id]['keywords']:
            keyword_counts[user_id]['keywords'][keyword] = 0

        count = content_lower.count(keyword)
        if count > 0:
            keyword_counts[user_id]['keywords'][keyword] += count
            found_keywords.append(keyword)
    
    
    if found_keywords:
        save_data(keyword_counts)
    
    
    await bot.process_commands(message)

@bot.tree.command(name='stats', description='View keyword statistics for yourself or another user')
@app_commands.describe(user='The user to view stats for (optional)')
async def stats(interaction: discord.Interaction, user: discord.Member = None):
    """Show keyword statistics for a user"""
    target_user = user if user else interaction.user
    user_id = str(target_user.id)
    
    if user_id not in keyword_counts:
        await interaction.response.send_message(f"No keyword data found for {target_user.name}")
        return
    
    user_data = keyword_counts[user_id]
    
    
    embed = discord.Embed(
        title=f"Keyword Stats for {target_user.name}",
        color=discord.Color.blue()
    )
    
    
    stats_text = ""
    for keyword, count in sorted(user_data['keywords'].items(), key=lambda x: x[1], reverse=True):
        if count > 0:  #omits any keywords that havent been said
            stats_text += f"**{keyword}**: {count}\n"
    
    embed.add_field(name="Keywords", value=stats_text if stats_text else "No keywords tracked yet", inline=False)
    
    total = sum(user_data['keywords'].values())
    embed.set_footer(text=f"Total keyword count: {total}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='leaderboard', description='View the leaderboard for a specific keyword or overall')
@app_commands.describe(keyword='The keyword to view leaderboard for (optional)')
async def leaderboard(interaction: discord.Interaction, keyword: str = None):
    """Show leaderboard for a specific keyword or overall"""
    if not keyword_counts:
        await interaction.response.send_message("No data available yet!")
        return
    
    if keyword:
        keyword = keyword.lower()
        if keyword not in KEYWORDS:
            await interaction.response.send_message(f"'{keyword}' is not a tracked keyword. Tracked keywords: {', '.join(KEYWORDS)}")
            return
        
        sorted_users = sorted(
            keyword_counts.items(),
            key=lambda x: x[1]['keywords'].get(keyword, 0),
            reverse=True
        )
        
        embed = discord.Embed(
            title=f"Leaderboard for '{keyword}'",
            color=discord.Color.gold()
        )
        
        leaderboard_text = ""
        for idx, (user_id, data) in enumerate(sorted_users[:10], 1):
            count = data['keywords'].get(keyword, 0)
            if count > 0:
                leaderboard_text += f"{idx}. {data['username']}: {count}\n"
        
        embed.add_field(
            name="Top Users",
            value=leaderboard_text if leaderboard_text else "No one has used this keyword yet",
            inline=False
        )
    else:
        
        user_totals = []
        for user_id, data in keyword_counts.items():
            total = sum(data['keywords'].values())
            user_totals.append((data['username'], total))
        
        user_totals.sort(key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(
            title="Overall Keyword Leaderboard",
            color=discord.Color.gold()
        )
        
        leaderboard_text = ""
        for idx, (username, total) in enumerate(user_totals[:10], 1):
            if total > 0:
                leaderboard_text += f"{idx}. {username}: {total}\n"
        
        embed.add_field(
            name="Top Users",
            value=leaderboard_text if leaderboard_text else "No data yet",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='keywords', description='Show list of tracked keywords')
async def keywords_command(interaction: discord.Interaction):
    """Show list of tracked keywords"""
    embed = discord.Embed(
        title="Tracked Keywords",
        description=", ".join(KEYWORDS),
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='addkeyword', description='Add a new keyword to track (Admin only)')
@app_commands.describe(keyword='The keyword to add')
async def addkeyword(interaction: discord.Interaction, keyword: str):
    """Add a new keyword to track (Admin only)"""
    if interaction.user.id not in ADMINS:
        await interaction.response.send_message("You dont have permission to do this.", ephemeral=True)
        return
    
    keyword = keyword.lower()
    if keyword in KEYWORDS:
        await interaction.response.send_message(f"'{keyword}' is already being tracked!")
        return
    
    KEYWORDS.append(keyword)
    
    with open(KEYWORDS_FILE, 'w') as f:
        f.write('\n'.join(KEYWORDS))
    
    for user_id in keyword_counts:
        keyword_counts[user_id]['keywords'][keyword] = 0
    
    save_data(keyword_counts)
    await interaction.response.send_message(f"'{keyword}' added")

@bot.tree.command(name='removekeyword', description='Remove a keyword from tracking (Admin only)')
@app_commands.describe(keyword='The keyword to remove')
async def removekeyword(interaction: discord.Interaction, keyword: str):
    """Remove a keyword from tracking (Admin only)"""
    if interaction.user.id not in ADMINS:
        await interaction.response.send_message("You dont have permission to do this.", ephemeral=True)
        return
    
    keyword = keyword.lower()
    if keyword not in KEYWORDS:
        await interaction.response.send_message(f"'{keyword}' is not being tracked!")
        return
    
    KEYWORDS.remove(keyword)
    
    with open(KEYWORDS_FILE, 'w') as f:
        f.write('\n'.join(KEYWORDS))
    
    for user_id in keyword_counts:
        if keyword in keyword_counts[user_id]['keywords']:
            del keyword_counts[user_id]['keywords'][keyword]
    
    save_data(keyword_counts)
    await interaction.response.send_message(f"'{keyword}' removed")

# run the bot
if __name__ == '__main__':
    TOKEN = load_config()
    
    if not TOKEN:
        print("=" * 60)
        print("ERROR: Bot token not found!")
        print("=" * 60)
        print(f"Please add your bot token to '{CONFIG_FILE}':")
        print("=" * 60)
        exit(1)
    
    print("Starting bot...")
    bot.run(TOKEN)