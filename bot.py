import discord
from discord.ext import commands
from datetime import datetime, time
import pytz

# 機器人設定
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# ===== 重要設定區 =====
# 你的時區（北美中部時間）
TIMEZONE = pytz.timezone('US/Mountain')

# 睡覺時間設定（24小時制）
SLEEP_START = time(21, 0)  # 晚上21:00開始睡覺
SLEEP_END = time(8, 0)     # 早上08:00起床

# ===== 監控設定 =====
# 監控的類別名稱
MONITORED_CATEGORIES = [
    '»» 。 。 。 。TICKET   。  。 。 。 ««',
]

# 監控的頻道名稱關鍵字
MONITORED_CHANNELS = [
    '│help',
    '-',
]

# 監控的 Forum 名稱
MONITORED_FORUM_NAMES = [
    '',
]

# 自動回覆訊息（完全按照你的內容）
AUTO_REPLY_MESSAGE = """
🌙 **Mint is either sleeping or at work**

Hello! Thank you for reaching out.

⏰ **Current time**: {current_time} (MST)
✅ **Ticket Response Time**：<t:1759600800:t> - <t:1759629600:t>

**Current status**: {status_message}

I will respond to your inquiry as soon as I'm available. {next_available}

**Note**: My job is not a ser schedule, so If I'm not responding during the day then I'm at work.

Thank you for your patience! 🌷
"""

# 已回覆的頻道記錄
replied_channels = set()

# ===== 功能函數 =====

def is_sleep_time():
    """檢查當前是否在睡覺時間"""
    now = datetime.now(TIMEZONE).time()
    
    if SLEEP_START < SLEEP_END:
        return now < SLEEP_START or now >= SLEEP_END
    else:
        return now >= SLEEP_START or now < SLEEP_END

def get_status_message():
    """獲取當前狀態訊息"""
    now = datetime.now(TIMEZONE)
    current_time = now.time()
    
    if current_time >= SLEEP_START or current_time < SLEEP_END:
        return f"I'm currently sleeping (Sleep time: {SLEEP_START.strftime('%H:%M')} - {SLEEP_END.strftime('%H:%M')})"
    else:
        return "I'm currently available but might be busy with other tasks"

def get_next_available_time():
    """獲取下次上線時間"""
    now = datetime.now(TIMEZONE)
    wake_datetime = now.replace(hour=SLEEP_END.hour, minute=SLEEP_END.minute, second=0, microsecond=0)
    
    if now.time() >= SLEEP_END and now.time() < SLEEP_START:
        return "I'm currently available!"
    
    if now.time() >= SLEEP_END:
        from datetime import timedelta
        wake_datetime += timedelta(days=1)
    
    return f"Expected response after **{wake_datetime.strftime('%m/%d %H:%M')}**."

def should_monitor_channel(channel):
    """判斷是否應該監控此頻道"""
    # 檢查 Forum
    if isinstance(channel, discord.ForumChannel):
        if MONITORED_FORUM_NAMES:
            return any(forum_name.lower() in channel.name.lower() for forum_name in MONITORED_FORUM_NAMES)
        return False
    
    # 檢查 Thread
    if isinstance(channel, discord.Thread):
        if channel.parent:
            if isinstance(channel.parent, discord.ForumChannel):
                if MONITORED_FORUM_NAMES:
                    return any(forum_name.lower() in channel.parent.name.lower() for forum_name in MONITORED_FORUM_NAMES)
            return should_monitor_channel(channel.parent)
        return False
    
    # 檢查頻道名稱
    channel_name_lower = channel.name.lower()
    if MONITORED_CHANNELS:
        if any(keyword.lower() in channel_name_lower for keyword in MONITORED_CHANNELS):
            return True
    
    # 檢查類別
    if hasattr(channel, 'category') and channel.category:
        category_name = channel.category.name
        if MONITORED_CATEGORIES:
            if any(cat.lower() in category_name.lower() for cat in MONITORED_CATEGORIES):
                return True
    
    return False

# ===== 機器人事件 =====

@bot.event
async def on_ready():
    """機器人啟動時執行"""
    print(f'✅ The robot is now online.：{bot.user.name}')
    print(f'📋 robot ID：{bot.user.id}')
    print(f'⏰ Current Time Zone：{TIMEZONE}')
    print(f'😴 Sleep Schedule：{SLEEP_START.strftime("%H:%M")} - {SLEEP_END.strftime("%H:%M")}')
    print(f'💼 Current Status：{"😴 Sleeping" if is_sleep_time() else "✅ Awake"}')
    print('\n🔍 Monitoring Settings：')
    print(f'  📁 Monitoring Category：{MONITORED_CATEGORIES if MONITORED_CATEGORIES else "無"}')
    print(f'  💬 Monitoring Channel：{MONITORED_CHANNELS if MONITORED_CHANNELS else "無"}')
    print(f'  📋 Monitoring Forum：{MONITORED_FORUM_NAMES if MONITORED_FORUM_NAMES else "無"}')
    print('=' * 50)

@bot.event
async def on_message(message):
    """當有新訊息時觸發"""
    if message.author.bot:
        await bot.process_commands(message)
        return
    
    channel = message.channel
    
    if not should_monitor_channel(channel):
        await bot.process_commands(message)
        return
    
    if channel.id in replied_channels:
        await bot.process_commands(message)
        return
    
    if not is_sleep_time():
        print(f'⏰ It is not bedtime; no automated replies will be sent.：{channel.name}')
        await bot.process_commands(message)
        return
    
    try:
        current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M')
        status_msg = get_status_message()
        next_available = get_next_available_time()
        
        reply_message = AUTO_REPLY_MESSAGE.format(
            current_time=current_time,
            status_message=status_msg,
            next_available=next_available
        )
        
        await channel.send(reply_message)
        replied_channels.add(channel.id)
        
        channel_type = "Forum Thread" if isinstance(channel, discord.Thread) and isinstance(channel.parent, discord.ForumChannel) else \
                       "Thread" if isinstance(channel, discord.Thread) else \
                       "Forum" if isinstance(channel, discord.ForumChannel) else "Channel"
        
        print(f'✅ An automated reply has been sent.')
        print(f'   Type：{channel_type}')
        print(f'   Name：{channel.name}')
        print(f'   User：{message.author.name}')
        if hasattr(channel, 'category') and channel.category:
            print(f'   Category：{channel.category.name}')
        
    except discord.Forbidden:
        print(f'❌ You do not have permission to send messages in this channel.：{channel.name}')
    except Exception as e:
        print(f'❌ An error occurred while sending the message.：{e}')
    
    await bot.process_commands(message)

@bot.event
async def on_thread_create(thread):
    """當 Forum 中創建新討論串時"""
    if isinstance(thread.parent, discord.ForumChannel):
        print(f'🆕 New Forum Thread Detected：{thread.name}')

# ===== 管理員指令 =====

@bot.command(name='status')
async def check_status(ctx):
    """檢查機器人狀態"""
    now = datetime.now(TIMEZONE)
    is_sleeping = is_sleep_time()
    
    embed = discord.Embed(
        title="🤖 Robot Status",
        color=discord.Color.orange() if is_sleeping else discord.Color.green(),
        timestamp=now
    )
    
    embed.add_field(
        name="📅 Current Time", 
        value=now.strftime('%Y-%m-%d %H:%M:%S'), 
        inline=False
    )
    
    embed.add_field(
        name="😴 Bedtime", 
        value=f"每天 {SLEEP_START.strftime('%H:%M')} - {SLEEP_END.strftime('%H:%M')}", 
        inline=False
    )
    
    status_emoji = "😴" if is_sleeping else "✅"
    status_text = "Asleep (auto-reply enabled)" if is_sleeping else "Awake (will not auto-reply)"
    embed.add_field(
        name="💼 Current Status", 
        value=f"{status_emoji} {status_text}", 
        inline=False
    )
    
    monitoring_info = []
    if MONITORED_CATEGORIES:
        monitoring_info.append(f"📁 Category：{len(MONITORED_CATEGORIES)} 個")
    if MONITORED_CHANNELS:
        monitoring_info.append(f"💬 Channel：{len(MONITORED_CHANNELS)} 個")
    if MONITORED_FORUM_NAMES:
        monitoring_info.append(f"📋 Forum：{len(MONITORED_FORUM_NAMES)} 個")
    
    if monitoring_info:
        embed.add_field(
            name="🔍 Monitoring Settings",
            value="\n".join(monitoring_info),
            inline=False
        )
    
    embed.add_field(
        name="📊 Statistics", 
        value=f"已回覆頻道數：{len(replied_channels)}", 
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='check')
async def check_channel(ctx):
    """檢查當前頻道是否會被監控"""
    channel = ctx.channel
    is_monitored = should_monitor_channel(channel)
    
    embed = discord.Embed(
        title="🔍 Channel Inspection",
        color=discord.Color.green() if is_monitored else discord.Color.red()
    )
    
    channel_type = "Forum Thread" if isinstance(channel, discord.Thread) and isinstance(channel.parent, discord.ForumChannel) else \
                   "Thread" if isinstance(channel, discord.Thread) else \
                   "Forum" if isinstance(channel, discord.ForumChannel) else \
                   "Text Channel"
    
    embed.add_field(name="Channel Name", value=channel.name, inline=False)
    embed.add_field(name="Channel Type", value=channel_type, inline=False)
    embed.add_field(name="Channel ID", value=str(channel.id), inline=False)
    
    if hasattr(channel, 'category') and channel.category:
        embed.add_field(name="Category", value=channel.category.name, inline=False)
    elif isinstance(channel, discord.Thread) and channel.parent:
        if isinstance(channel.parent, discord.ForumChannel):
            embed.add_field(name="Forum", value=channel.parent.name, inline=False)
        else:
            embed.add_field(name="Parent Channel", value=channel.parent.name, inline=False)
    
    embed.add_field(
        name="Monitoring Status",
        value=f"{'✅ will be monitored' if is_monitored else '❌ 不會被監控'}",
        inline=False
    )
    
    if channel.id in replied_channels:
        embed.add_field(
            name="Reply Status",
            value="⚠️ This channel has already responded (will not auto-reply again).",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='list')
@commands.has_permissions(administrator=True)
async def list_monitored(ctx):
    """列出所有監控設定"""
    embed = discord.Embed(
        title="📋 Monitoring Configuration Checklist",
        color=discord.Color.blue()
    )
    
    if MONITORED_CATEGORIES:
        categories_text = "\n".join([f"• {cat}" for cat in MONITORED_CATEGORIES])
        embed.add_field(name="📁 Categories of Monitoring", value=categories_text, inline=False)
    
    if MONITORED_CHANNELS:
        channels_text = "\n".join([f"• {ch}" for ch in MONITORED_CHANNELS])
        embed.add_field(name="💬 Monitored channels", value=channels_text, inline=False)
    
    if MONITORED_FORUM_NAMES:
        forums_text = "\n".join([f"• {forum}" for forum in MONITORED_FORUM_NAMES])
        embed.add_field(name="📋 Monitoring Forum", value=forums_text, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='clear')
@commands.has_permissions(administrator=True)
async def clear_replied(ctx):
    """清除已回覆的頻道記錄"""
    count = len(replied_channels)
    replied_channels.clear()
    await ctx.send(f'✅ {count} channel reply records have been cleared.')

@bot.command(name='test')
@commands.has_permissions(administrator=True)
async def test_reply(ctx):
    """測試自動回覆訊息"""
    current_time = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M')
    status_msg = get_status_message()
    next_available = get_next_available_time()
    
    message = AUTO_REPLY_MESSAGE.format(
        current_time=current_time,
        status_message=status_msg,
        next_available=next_available
    )
    
    await ctx.send(message)
    await ctx.send('⬆️ The above is a preview of the automated reply message.')

@bot.command(name='add')
@commands.has_permissions(administrator=True)
async def add_channel_to_replied(ctx):
    """將當前頻道加入已回覆清單"""
    if ctx.channel.id in replied_channels:
        await ctx.send('⚠️ This channel has been added to the replied list.')
    else:
        replied_channels.add(ctx.channel.id)
        await ctx.send('✅ This channel has been added to the replied list.')

@bot.command(name='remove')
@commands.has_permissions(administrator=True)
async def remove_channel_from_replied(ctx):
    """將當前頻道從已回覆清單移除"""
    if ctx.channel.id not in replied_channels:
        await ctx.send('⚠️ This channel is not in the replied list.')
    else:
        replied_channels.remove(ctx.channel.id)
        await ctx.send('✅ This channel has been removed from the replied list.')

@bot.command(name='help_bot')
async def help_command(ctx):
    """顯示機器人指令幫助"""
    embed = discord.Embed(
        title="🤖 Robot Command Manual",
        description="以下是可用的指令：",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="!status", value="Check the robot's current status", inline=False)
    embed.add_field(name="!check", value="Check whether the current channel is being monitored.", inline=False)
    embed.add_field(name="!list (管理員)", value="List all monitoring settings", inline=False)
    embed.add_field(name="!test (管理員)", value="Testing automated reply messages", inline=False)
    embed.add_field(name="!clear (管理員)", value="Clear replied records", inline=False)
    embed.add_field(name="!add (管理員)", value="Mark current channel as replied", inline=False)
    embed.add_field(name="!remove (管理員)", value="Remove current channel marker", inline=False)
    embed.add_field(name="!help_bot", value="Display this help message", inline=False)
    
    await ctx.send(embed=embed)

# ===== 啟動機器人 =====
if __name__ == '__main__':
    import os
    
    print('🚀 Starting up the robot...')
    
    TOKEN = os.environ.get('DISCORD_TOKEN')
    
    if not TOKEN:
        print('❌ 錯誤：找不到 DISCORD_TOKEN 環境變數')
        print('請在 Render 控制台設定 DISCORD_TOKEN')
        exit(1)
    else:
        print('✅ Token 已載入')
        print(f'✅ Token 長度：{len(TOKEN)} 字元')
        bot.run(TOKEN)