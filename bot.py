import discord
from discord.ext import commands, tasks
import os
import random
import aiohttp
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
import tweepy
import re
import json

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# ---------- TWITTER BEARER TOKEN ----------
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
if not BEARER_TOKEN:
    # ⚠️ REPLACE THIS WITH YOUR ACTUAL TOKEN (keep the quotes)
    BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANIZ%2BgEAAAAAMO6tGMGBQyQf7K9Ap1gweXR3yQs%3DVYFkTPddMR7wl4IQQSWcNzWFQgZmN1iY1ThzO5IfaHnnYheTcb"

# Bot configuration
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

# Bot info
APP_VERSION = "2.1.0"
SUPPORTED_EXCHANGES = ["Binance", "Bybit", "Coinbase", "Kraken", "KuCoin", "OKX", "Hyperliquid"]

# ============================================
# TWITTER FUD / LARGE WITHDRAWAL ALERTS (VERY SENSITIVE)
# ============================================

# Check if token is valid
if BEARER_TOKEN and BEARER_TOKEN != "your_twitter_bearer_token_here":
    TWITTER_CLIENT = tweepy.Client(bearer_token=BEARER_TOKEN)
else:
    TWITTER_CLIENT = None

PROCESSED_FILE = "processed_tweets.json"

# EXTREMELY LOW THRESHOLDS – catch almost any mention
WITHDRAWAL_THRESHOLD = {
    "BTC": 1,          # 1 BTC – very low
    "ETH": 10,         # 10 ETH
    "USDT": 10000,     # 10k USDT
    "USDC": 10000,
    "DAI": 10000,
    "XRP": 1000,
    "ADA": 1000,
    "SOL": 100,
    "DOT": 100,
    "AVAX": 100
}

# Much broader FUD keywords
FUD_TRIGGER_WORDS = [
    "bank run",
    "insolvent",
    "freeze withdrawals",
    "halt withdrawals",
    "collapse",
    "hack",
    "exploit",
    "panic",
    "suspends withdrawals",
    "liquidity crisis",
    "scam",
    "rug",
    "exit scam",
    "bankrupt",
    "withdrawal issue",
    "can't withdraw",
    "withdrawal delay"
]

# Status tracking
fud_last_run = None
fud_last_count = 0

def load_processed_ids():
    try:
        with open(PROCESSED_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_processed_ids(ids):
    with open(PROCESSED_FILE, "w") as f:
        json.dump(list(ids), f)

def analyze_tweet(text):
    """
    Returns: (amount, unit, reason)
    """
    # 1. Check for a numeric withdrawal
    pattern = r'(\d{1,3}(?:,\d{3})*)\s*(BTC|ETH|USDT|USDC|DAI|XRP|ADA|SOL|DOT|AVAX)'
    for match in re.finditer(pattern, text, re.IGNORECASE):
        raw = match.group(1).replace(",", "")
        amount = float(raw)
        unit = match.group(2).upper()
        if amount >= WITHDRAWAL_THRESHOLD.get(unit, 0):
            return amount, unit, "💰 Large Withdrawal"
    
    # 2. If no amount found, check for FUD keywords
    text_lower = text.lower()
    for word in FUD_TRIGGER_WORDS:
        if word in text_lower:
            return None, None, "🔥 FUD Panic Alert"
    
    return None, None, None

def fetch_twitter_fud_tweets():
    """Synchronous fetch – runs in a thread."""
    if not TWITTER_CLIENT:
        return []
    
    # Very broad query – catches almost anything about exchanges and withdrawals/FUD
    query = (
        "(binance OR coinbase OR kraken OR bybit OR ftx OR okx OR huobi OR kucoin OR gate.io OR crypto.com OR exchange) "
        "AND (withdraw* OR outflow* OR deposit* OR transfer* OR fud OR panic OR bank run OR insolvent OR freeze OR halt OR collapse OR hack OR scam OR rug) "
        "-is:retweet -is:reply lang:en"
    )
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    try:
        tweets = TWITTER_CLIENT.search_recent_tweets(
            query=query,
            tweet_fields=["created_at", "author_id"],
            max_results=100,
            start_time=start_time.isoformat(timespec="seconds") + "Z",
            end_time=end_time.isoformat(timespec="seconds") + "Z"
        )
        count = len(tweets.data) if tweets.data else 0
        print(f"🔍 Twitter fetch: {count} tweets found in the last 24h.")
        return tweets.data if tweets.data else []
    except Exception as e:
        print(f"❌ Twitter API error: {e}")
        return []

async def get_twitter_alerts():
    """Async wrapper – fetches new tweets and filters them."""
    processed = load_processed_ids()
    new_alerts = []
    tweets = await asyncio.to_thread(fetch_twitter_fud_tweets)
    
    for tweet in tweets:
        if tweet.id in processed:
            continue
        
        amount, unit, reason = analyze_tweet(tweet.text)
        
        if amount:
            new_alerts.append({
                "id": tweet.id,
                "text": tweet.text[:200],
                "url": f"https://twitter.com/i/web/status/{tweet.id}",
                "detail": f"{amount:,.0f} {unit} - {reason}",
                "created_at": tweet.created_at
            })
        elif unit is None and reason:
            new_alerts.append({
                "id": tweet.id,
                "text": tweet.text[:200],
                "url": f"https://twitter.com/i/web/status/{tweet.id}",
                "detail": reason,
                "created_at": tweet.created_at
            })
        
        processed.add(tweet.id)
    
    save_processed_ids(processed)
    return new_alerts

# ============================================
# BACKGROUND TASKS (AUTO-ALERTS)
# ============================================

@tasks.loop(minutes=5)
async def check_exchange_status_auto():
    """Auto-check exchange status every 5 minutes with alerts"""
    channel_id = os.getenv('ALERT_CHANNEL_ID')
    if not channel_id:
        return
    channel = bot.get_channel(int(channel_id))
    if not channel:
        return
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.binance.com/api/v3/ping", timeout=5) as resp:
                if resp.status != 200:
                    await channel.send(f"🔴 **ALERT:** Binance is having issues! Status: {resp.status}")
    except asyncio.TimeoutError:
        await channel.send("🔴 **ALERT:** Binance is not responding (timeout)!")
    except Exception as e:
        await channel.send(f"🔴 **ALERT:** Binance error: {str(e)[:50]}")

@tasks.loop(hours=1)
async def send_daily_report():
    """Send a daily report every hour"""
    channel_id = os.getenv('ALERT_CHANNEL_ID')
    if not channel_id:
        return
    channel = bot.get_channel(int(channel_id))
    if not channel:
        return
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd") as resp:
                data = await resp.json()
                btc_price = data.get('bitcoin', {}).get('usd', 'N/A')
                await channel.send(f"📊 **Daily Report**\nBitcoin: ${btc_price}\nAll systems operational")
    except:
        await channel.send("⚠️ Could not fetch price data")

@tasks.loop(hours=24)
async def send_twitter_fud_report():
    """Post Twitter FUD/large-withdrawal alerts every 24h."""
    global fud_last_run, fud_last_count
    if not TWITTER_CLIENT:
        return
    channel_id = os.getenv('ALERT_CHANNEL_ID')
    if not channel_id:
        return
    channel = bot.get_channel(int(channel_id))
    if not channel:
        return
    alerts = await get_twitter_alerts()
    fud_last_run = datetime.utcnow()
    fud_last_count = len(alerts)
    if not alerts:
        return
    embed = discord.Embed(
        title="🚨 Daily Exchange FUD & Large Withdrawal Alerts",
        description="Tweets mentioning large outflows or FUD in the last 24 hours:",
        color=0xff5500,
        timestamp=datetime.utcnow()
    )
    for alert in alerts[:10]:
        embed.add_field(
            name=f"{alert['detail']}",
            value=f"{alert['text']}... [Link]({alert['url']})",
            inline=False
        )
    embed.set_footer(text="Alerts auto-generated every 24h")
    await channel.send(embed=embed)

# ============================================
# EVENTS
# ============================================

@bot.event
async def on_ready():
    print(f'✅ Coin Escape Bot is online!')
    print(f'📊 Logged in as: {bot.user}')
    print(f'🌐 Connected to {len(bot.guilds)} servers')
    
    check_exchange_status_auto.start()
    send_daily_report.start()
    if TWITTER_CLIENT:
        send_twitter_fud_report.start()
        print("✅ Twitter FUD alert system started.")
    else:
        print("⚠️ Twitter client not configured – FUD alerts disabled.")
    
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="crypto markets | !help"
    ))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❌ Unknown command. Type `!help` for available commands.")
    else:
        await ctx.send(f"❌ Error: {str(error)}")
        print(f"Error: {error}")

# ============================================
# BASIC COMMANDS (existing – kept unchanged)
# ============================================

# ... (all your existing commands: ping, about, security, help, testcmds, guide, faq, status, version, coinflip, server, exchanges, exchange_status, coins, price, btc, eth, sol, withdraw_status, track, support)

# ============================================
# TEST COMMAND FOR TWITTER API
# ============================================

@bot.command()
async def test_twitter(ctx):
    """Test if Twitter API returns any tweets."""
    if not TWITTER_CLIENT:
        await ctx.send("❌ Twitter client not configured. Please set BEARER_TOKEN.")
        return
    try:
        tweets = TWITTER_CLIENT.search_recent_tweets(
            query="crypto",
            max_results=5
        )
        count = len(tweets.data) if tweets.data else 0
        await ctx.send(f"✅ Twitter API is working! Found {count} tweets about 'crypto'.")
    except Exception as e:
        await ctx.send(f"❌ Twitter API error: {e}")

# ============================================
# FUD COMMANDS
# ============================================

@bot.command()
async def fud(ctx):
    """Manually check for recent exchange FUD/large withdrawal tweets."""
    if not TWITTER_CLIENT:
        await ctx.send("❌ Twitter API not configured. Please set BEARER_TOKEN.")
        return
    await ctx.send("🔍 Scanning Twitter for exchange FUD and large withdrawals...")
    alerts = await get_twitter_alerts()
    if not alerts:
        await ctx.send("✅ No new large withdrawal or FUD tweets in the last 24 hours.")
        return
    embed = discord.Embed(
        title="🚨 Exchange FUD & Large Withdrawal Alerts",
        description=f"Found **{len(alerts)}** new alerts:",
        color=0xff5500,
        timestamp=datetime.utcnow()
    )
    for alert in alerts[:10]:
        embed.add_field(
            name=f"{alert['detail']}",
            value=f"{alert['text']}... [Link]({alert['url']})",
            inline=False
        )
    if len(alerts) > 10:
        embed.set_footer(text=f"Showing first 10 of {len(alerts)} alerts")
    await ctx.send(embed=embed)

@bot.command()
async def fud_status(ctx):
    """Show status of the FUD alert system."""
    embed = discord.Embed(
        title="📊 FUD Alert System Status",
        color=0x3498db
    )
    if fud_last_run:
        embed.add_field(
            name="Last Auto-Run",
            value=f"{fud_last_run.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            inline=False
        )
        embed.add_field(
            name="Tweets Found (last run)",
            value=str(fud_last_count),
            inline=True
        )
    else:
        embed.add_field(
            name="Status",
            value="No auto-run has occurred yet.",
            inline=False
        )
    embed.add_field(
        name="Auto-Interval",
        value="Every 24 hours",
        inline=True
    )
    embed.add_field(
        name="Manual Command",
        value="!fud",
        inline=True
    )
    embed.add_field(
        name="Twitter Client",
        value="✅ Configured" if TWITTER_CLIENT else "❌ Not Configured",
        inline=True
    )
    embed.set_footer(text="processed_tweets.json tracks seen tweets")
    await ctx.send(embed=embed)

# ============================================
# RUN THE BOT
# ============================================

if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERROR: No Discord token found! Create a .env file with DISCORD_TOKEN=your_token")
    else:
        print("🚀 Starting Coin Escape Bot v2.1...")
        bot.run(TOKEN)
