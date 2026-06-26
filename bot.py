import discord
from discord.ext import commands
import os
import random
import aiohttp
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot configuration
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Bot version
APP_VERSION = "1.0.0"
SUPPORTED_EXCHANGES = ["Binance", "Bybit", "Coinbase", "Kraken", "KuCoin", "OKX", "Deribit"]

# ============================================
# EVENTS
# ============================================

@bot.event
async def on_ready():
    print(f'✅ Coin Escape Bot is online!')
    print(f'📊 Logged in as: {bot.user}')
    print(f'🌐 Connected to {len(bot.guilds)} servers')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="for !commands | !help"
    ))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❌ Unknown command. Type `!commands` for available commands.")
    else:
        await ctx.send(f"❌ Error: {str(error)}")
        print(f"Error: {error}")

# ============================================
# BASIC COMMANDS
# ============================================

@bot.command()
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency: {latency}ms")

@bot.command()
async def about(ctx):
    """About Coin Escape"""
    embed = discord.Embed(
        title="🪙 Coin Escape",
        description="Emergency panic withdrawal app for crypto exchanges. "
                    "Connect your exchange API keys and drain funds to self-custody "
                    "in one action when an exchange looks compromised.",
        color=0x00ff88
    )
    embed.add_field(name="Version", value=APP_VERSION, inline=True)
    embed.add_field(name="Security", value="AES-256-GCM encrypted on-device", inline=True)
    embed.add_field(name="GitHub", value="[View Source](https://github.com/chezdon0074/Coin-Escape-bot)", inline=False)
    embed.set_footer(text="🚀 Built for crypto security")
    await ctx.send(embed=embed)

@bot.command()
async def exchanges(ctx):
    """List supported exchanges"""
    exchanges = "\n".join([f"• {ex}" for ex in SUPPORTED_EXCHANGES])
    embed = discord.Embed(
        title="🏦 Supported Exchanges",
        description=exchanges,
        color=0x3498db
    )
    embed.set_footer(text=f"{len(SUPPORTED_EXCHANGES)} exchanges supported")
    await ctx.send(embed=embed)

@bot.command()
async def security(ctx):
    """Security model explanation"""
    embed = discord.Embed(
        title="🔐 Security Model",
        description="Coin Escape takes security seriously:",
        color=0x2ecc71
    )
    embed.add_field(
        name="🔒 On-Device Encryption",
        value="Credentials are encrypted using AES-256-GCM and stored in `expo-secure-store`.",
        inline=False
    )
    embed.add_field(
        name="🧠 Session Key",
        value="The session key lives only in memory—never persisted to disk.",
        inline=False
    )
    embed.add_field(
        name="🧪 Dry Run Mode",
        value="Test withdrawals without moving real funds before enabling Real Withdrawal.",
        inline=False
    )
    embed.set_footer(text="Your keys, your control")
    await ctx.send(embed=embed)

@bot.command()
async def guide(ctx):
    """Getting started guide"""
    embed = discord.Embed(
        title="📖 Getting Started",
        description="Follow the complete setup guide on GitHub:",
        color=0xe67e22
    )
    embed.add_field(
        name="🔗 Guide Link",
        value="https://github.com/chezdon0074/Coin-Escape-bot#readme",
        inline=False
    )
    embed.add_field(
        name="📱 Mobile App",
        value="Available for iOS and Android via Expo",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command()
async def faq(ctx):
    """Frequently asked questions"""
    embed = discord.Embed(
        title="❓ Frequently Asked Questions",
        color=0x9b59b6
    )
    embed.add_field(
        name="What is Coin Escape?",
        value="A panic withdrawal app that helps you quickly move funds from exchanges to self-custody.",
        inline=False
    )
    embed.add_field(
        name="Is it safe?",
        value="✅ Yes—keys are encrypted on-device. No server-side storage of credentials.",
        inline=False
    )
    embed.add_field(
        name="Which exchanges are supported?",
        value=f"{', '.join(SUPPORTED_EXCHANGES)}",
        inline=False
    )
    embed.add_field(
        name="Can I test it first?",
        value="✅ Yes! Use Dry Run mode to simulate withdrawals without moving real funds.",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command()
async def status(ctx):
    """Check bot and app status"""
    embed = discord.Embed(
        title="🟢 Status",
        description="All systems operational",
        color=0x2ecc71
    )
    embed.add_field(name="Bot Status", value="✅ Online", inline=True)
    embed.add_field(name="Version", value=APP_VERSION, inline=True)
    embed.add_field(name="Connected Servers", value=str(len(bot.guilds)), inline=True)
    embed.set_footer(text=f"Latency: {round(bot.latency * 1000)}ms")
    await ctx.send(embed=embed)

@bot.command()
async def version(ctx):
    """Show current version"""
    await ctx.send(f"📦 Coin Escape v{APP_VERSION}")

@bot.command()
async def commands(ctx):
    """List all available commands"""
    embed = discord.Embed(
        title="📋 Coin Escape Commands",
        description="Here are all available commands:",
        color=0x00ff88
    )
    embed.add_field(
        name="📊 Basic",
        value="`!ping` - Check latency\n"
              "`!about` - About Coin Escape\n"
              "`!version` - Show version\n"
              "`!status` - Bot status\n"
              "`!commands` - Show this menu",
        inline=False
    )
    embed.add_field(
        name="🔐 Security & Info",
        value="`!security` - Security model\n"
              "`!exchanges` - Supported exchanges\n"
              "`!faq` - Frequently asked questions\n"
              "`!guide` - Getting started guide",
        inline=False
    )
    embed.add_field(
        name="🎮 Fun",
        value="`!coinflip` - Flip a coin\n"
              "`!server` - Server info",
        inline=False
    )
    embed.set_footer(text="🪙 Coin Escape Bot")
    await ctx.send(embed=embed)

# ============================================
# FUN COMMANDS
# ============================================

@bot.command()
async def coinflip(ctx):
    """Flip a coin"""
    result = random.choice(["Heads", "Tails"])
    await ctx.send(f"🪙 The coin landed on **{result}**!")

@bot.command()
async def server(ctx):
    """Server info"""
    guild = ctx.guild
    embed = discord.Embed(
        title=f"🛡️ {guild.name}",
        description="Server information:",
        color=0x3498db
    )
    embed.add_field(name="Owner", value=str(guild.owner), inline=True)
    embed.add_field(name="Members", value=str(guild.member_count), inline=True)
    embed.add_field(name="Channels", value=str(len(guild.channels)), inline=True)
    embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)

# ============================================
# RUN THE BOT
# ============================================

if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERROR: No token found! Create a .env file with DISCORD_TOKEN=your_token")
    else:
        print("🚀 Starting Coin Escape Bot...")
        bot.run(TOKEN)
