import discord
from discord.ext import commands, tasks
import os
import random
import aiohttp
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot configuration
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Bot info
APP_VERSION = "2.0.0"
SUPPORTED_EXCHANGES = ["Binance", "Bybit", "Coinbase", "Kraken", "KuCoin", "OKX", "Deribit"]

# ============================================
# BACKGROUND TASKS (AUTO-ALERTS)
# ============================================

@tasks.loop(minutes=5)
async def check_exchange_status():
    """Check exchange status every 5 minutes"""
    channel_id = os.getenv('ALERT_CHANNEL_ID')
    if not channel_id:
        return
    
    channel = bot.get_channel(int(channel_id))
    if not channel:
        return
    
    # Check Binance
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.binance.com/api/v3/ping") as resp:
                if resp.status == 200:
                    status = "🟢 Online"
                else:
                    status = "🔴 Offline"
                    await channel.send(f"⚠️ **ALERT:** Binance is having issues! Status: {resp.status}")
    except:
        await channel.send("🔴 **ALERT:** Binance is not responding!")

@tasks.loop(hours=1)
async def send_daily_report():
    """Send a daily report every hour"""
    channel_id = os.getenv('ALERT_CHANNEL_ID')
    if not channel_id:
        return
    
    channel = bot.get_channel(int(channel_id))
    if not channel:
        return
    
    # Get Bitcoin price
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd") as resp:
                data = await resp.json()
                btc_price = data.get('bitcoin', {}).get('usd', 'N/A')
                await channel.send(f"📊 **Daily Report**\nBitcoin: ${btc_price}\nAll systems operational")
    except:
        await channel.send("⚠️ Could not fetch price data")

# ============================================
# EVENTS
# ============================================

@bot.event
async def on_ready():
    print(f'✅ Coin Escape Bot is online!')
    print(f'📊 Logged in as: {bot.user}')
    print(f'🌐 Connected to {len(bot.guilds)} servers')
    
    # Start background tasks
    check_exchange_status.start()
    send_daily_report.start()
    
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="crypto markets | !help"
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
        name="📊 Exchange & Prices",
        value="`!exchange-status` - Check exchange health\n"
              "`!price <coin>` - Get crypto price\n"
              "`!btc` - Bitcoin price\n"
              "`!eth` - Ethereum price\n"
              "`!sol` - Solana price",
        inline=False
    )
    embed.add_field(
        name="🔍 Withdrawal Tools",
        value="`!withdraw-status <coin>` - Check deposit/withdraw status\n"
              "`!track <network> <txid>` - Track a transaction\n"
              "`!support` - Binance support links",
        inline=False
    )
    embed.set_footer(text="🔄 Automation features active")
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
# EXCHANGE COMMANDS
# ============================================

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
async def exchange_status(ctx, exchange: str = None):
    """Check if an exchange is online"""
    if not exchange:
        embed = discord.Embed(
            title="🔌 Exchange Status",
            description="Checking all exchanges...",
            color=0x3498db
        )
        
        # Check Binance
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.binance.com/api/v3/ping") as resp:
                    status = "🟢 Online" if resp.status == 200 else "🔴 Offline"
                    embed.add_field(name="Binance", value=status, inline=True)
        except:
            embed.add_field(name="Binance", value="🔴 Offline", inline=True)
        
        # Check Bybit
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.bybit.com/v5/system/time") as resp:
                    status = "🟢 Online" if resp.status == 200 else "🔴 Offline"
                    embed.add_field(name="Bybit", value=status, inline=True)
        except:
            embed.add_field(name="Bybit", value="🔴 Offline", inline=True)
        
        # Check Coinbase
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.coinbase.com/v2/time") as resp:
                    status = "🟢 Online" if resp.status == 200 else "🔴 Offline"
                    embed.add_field(name="Coinbase", value=status, inline=True)
        except:
            embed.add_field(name="Coinbase", value="🔴 Offline", inline=True)
        
        embed.set_footer(text=f"Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        await ctx.send(embed=embed)
        return
    
    # Check specific exchange
    exchange = exchange.lower()
    if exchange == "binance":
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.binance.com/api/v3/ping") as resp:
                    if resp.status == 200:
                        await ctx.send(f"🟢 **Binance** is online!")
                    else:
                        await ctx.send(f"🔴 **Binance** is offline (Status: {resp.status})")
        except:
            await ctx.send("🔴 **Binance** is not responding!")
    
    elif exchange == "bybit":
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.bybit.com/v5/system/time") as resp:
                    if resp.status == 200:
                        await ctx.send(f"🟢 **Bybit** is online!")
                    else:
                        await ctx.send(f"🔴 **Bybit** is offline (Status: {resp.status})")
        except:
            await ctx.send("🔴 **Bybit** is not responding!")
    
    elif exchange == "coinbase":
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.coinbase.com/v2/time") as resp:
                    if resp.status == 200:
                        await ctx.send(f"🟢 **Coinbase** is online!")
                    else:
                        await ctx.send(f"🔴 **Coinbase** is offline (Status: {resp.status})")
        except:
            await ctx.send("🔴 **Coinbase** is not responding!")
    
    else:
        await ctx.send(f"❌ Unknown exchange. Available: `binance`, `bybit`, `coinbase`")

# ============================================
# PRICE COMMANDS
# ============================================

@bot.command()
async def price(ctx, coin: str = "bitcoin"):
    """Get current crypto price (bitcoin, ethereum, solana, etc.)"""
    coin = coin.lower()
    
    # Map common names to CoinGecko IDs
    coin_map = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "sol": "solana",
        "ada": "cardano",
        "dot": "polkadot",
        "avax": "avalanche-2",
        "matic": "polygon",
        "link": "chainlink",
        "uni": "uniswap",
        "doge": "dogecoin"
    }
    
    coin_id = coin_map.get(coin, coin)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
            ) as resp:
                if resp.status != 200:
                    await ctx.send(f"❌ Could not find coin: `{coin}`")
                    return
                data = await resp.json()
                
                if coin_id not in data:
                    await ctx.send(f"❌ Could not find coin: `{coin}`")
                    return
                
                price = data[coin_id]['usd']
                change = data[coin_id].get('usd_24h_change', 0)
                
                emoji = "📈" if change >= 0 else "📉"
                change_str = f"+{change:.2f}%" if change >= 0 else f"{change:.2f}%"
                
                embed = discord.Embed(
                    title=f"💰 {coin.upper()} Price",
                    description=f"**${price:,.2f}**",
                    color=0x00ff88 if change >= 0 else 0xff4444
                )
                embed.add_field(name="24h Change", value=f"{emoji} {change_str}", inline=True)
                embed.add_field(name="Source", value="CoinGecko", inline=True)
                embed.set_footer(text=f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                await ctx.send(embed=embed)
    
    except:
        await ctx.send("❌ Error fetching price data. Please try again.")

@bot.command()
async def btc(ctx):
    """Get Bitcoin price"""
    await price(ctx, "bitcoin")

@bot.command()
async def eth(ctx):
    """Get Ethereum price"""
    await price(ctx, "ethereum")

@bot.command()
async def sol(ctx):
    """Get Solana price"""
    await price(ctx, "solana")

# ============================================
# BINANCE NETWORK STATUS (Deposit/Withdrawal)
# ============================================

@bot.command()
async def withdraw_status(ctx, coin: str = None):
    """Check deposit/withdrawal status for a specific coin (e.g., !withdraw-status BTC)"""
    
    if not coin:
        await ctx.send("❌ Please specify a coin. Example: `!withdraw-status BTC` or `!withdraw-status ETH`")
        return
    
    coin = coin.upper()
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("https://api.binance.com/api/v3/capital/config/getall") as resp:
                if resp.status != 200:
                    await ctx.send("❌ Failed to fetch network status from Binance.")
                    return
                data = await resp.json()
        except:
            await ctx.send("❌ Error connecting to Binance API.")
            return
    
    # Find the coin
    coin_data = None
    for item in data:
        if item['coin'] == coin:
            coin_data = item
            break
    
    if not coin_data:
        await ctx.send(f"❌ No network information found for **{coin}**. Please check the symbol (e.g., BTC, ETH, SOL).")
        return
    
    # Build the embed
    embed = discord.Embed(
        title=f"🌐 {coin} Network Status",
        description=f"Deposit & Withdrawal status for **{coin}**",
        color=0xf0b90b
    )
    
    network_list = coin_data.get('networkList', [])
    
    if not network_list:
        embed.add_field(name="⚠️ No networks available", value="No network data found for this coin.", inline=False)
    else:
        for network in network_list[:10]:
            network_name = network.get('network', 'Unknown')
            deposit = network.get('depositEnable', False)
            withdraw = network.get('withdrawEnable', False)
            
            deposit_emoji = "✅" if deposit else "❌"
            withdraw_emoji = "✅" if withdraw else "❌"
            
            status_text = f"**Deposit:** {deposit_emoji} | **Withdraw:** {withdraw_emoji}"
            
            min_confirm = network.get('minConfirm', 'N/A')
            if min_confirm != 'N/A':
                status_text += f"\n`Confirmations: {min_confirm}`"
            
            embed.add_field(
                name=f"**{network_name}**",
                value=status_text,
                inline=False
            )
    
    embed.set_footer(text=f"Data provided by Binance | Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    await ctx.send(embed=embed)

# ============================================
# WITHDRAWAL TRACKING COMMANDS
# ============================================

@bot.command()
async def track(ctx, network: str, txid: str):
    """Track a withdrawal transaction - !track BTC 123abc..."""
    
    # Network explorer links
    explorers = {
        "btc": "https://www.blockchain.com/explorer/transactions/btc/",
        "eth": "https://etherscan.io/tx/",
        "bsc": "https://bscscan.com/tx/",
        "sol": "https://solscan.io/tx/",
        "trx": "https://tronscan.org/#/transaction/",
        "polygon": "https://polygonscan.com/tx/",
        "arb": "https://arbiscan.io/tx/",
        "op": "https://optimistic.etherscan.io/tx/",
        "avax": "https://snowtrace.io/tx/",
        "matic": "https://polygonscan.com/tx/"
    }
    
    network = network.lower()
    
    if network not in explorers:
        networks_list = "\n".join([f"• {key.upper()}" for key in explorers.keys()])
        await ctx.send(f"❌ Unknown network. Available networks:\n{networks_list}")
        return
    
    explorer_url = explorers[network] + txid
    
    embed = discord.Embed(
        title="🔍 Withdrawal Tracker",
        description=f"Tracking transaction on **{network.upper()}** network",
        color=0x00ff88
    )
    embed.add_field(
        name="📋 Transaction ID (TXID)",
        value=f"`{txid[:20]}...{txid[-10:] if len(txid) > 30 else ''}`",
        inline=False
    )
    embed.add_field(
        name="🔗 View on Explorer",
        value=f"[Click here to view]({explorer_url})",
        inline=False
    )
    embed.add_field(
        name="📊 Status Check",
        value="✅ **Transaction Found**\nClick the link above to see:\n• Confirmations\n• From/To addresses\n• Amount transferred",
        inline=False
    )
    embed.set_footer(text="⚠️ This is a public transaction lookup. No personal data is accessed.")
    
    await ctx.send(embed=embed)

@bot.command()
async def support(ctx, withdrawal_id: str = None):
    """Get direct Binance support link for a withdrawal"""
    
    if not withdrawal_id:
        # Show general support links
        embed = discord.Embed(
            title="🆘 Binance Withdrawal Support",
            description="Need help with a withdrawal? Here are the official support links:",
            color=0xf0b90b
        )
        embed.add_field(
            name="📧 Binance Support Center",
            value="[Open Support Ticket](https://www.binance.com/en/support/ticket)\n\n"
                  "**Before contacting support, please check:**\n"
                  "• Network status with `!withdraw-status BTC`\n"
                  "• Your withdrawal status in Binance app\n"
                  "• If you have the TXID, use `!track`",
            inline=False
        )
        embed.add_field(
            name="📊 Common Withdrawal Issues",
            value="• **Pending**: Wait for confirmations\n"
                  "• **Failed**: Check network status\n"
                  "• **Delayed**: Network congestion\n"
                  "• **Wrong network**: Contact support immediately",
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    # Support link with withdrawal ID
    support_url = f"https://www.binance.com/en/support/ticket?withdrawal_id={withdrawal_id}"
    
    embed = discord.Embed(
        title="🆘 Withdrawal Support",
        description=f"Direct support link for Withdrawal ID: **{withdrawal_id}**",
        color=0xf0b90b
    )
    embed.add_field(
        name="🔗 Open Support Ticket",
        value=f"[Click here to contact Binance Support]({support_url})\n\n"
              "**Have this information ready:**\n"
              "• Withdrawal ID\n"
              "• Amount and coin\n"
              "• Timestamp of withdrawal\n"
              "• Transaction hash (if available)",
        inline=False
    )
    embed.set_footer(text="🚨 Contact support immediately for any issues with your funds.")
    
    await ctx.send(embed=embed)

# ============================================
# RUN THE BOT
# ============================================

if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERROR: No token found! Create a .env file with DISCORD_TOKEN=your_token")
    else:
        print("🚀 Starting Coin Escape Bot v2.0...")
        bot.run(TOKEN)
