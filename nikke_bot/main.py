import os
import asyncio
import discord
from discord.ext import tasks, commands
from config import TOKEN, CHANNEL_ID, CHECK_INTERVAL, IMPORTANT_KEYWORDS
from twitter_api_helper import has_new_tweet, RateLimitError, get_latest_tweet
from rss_fallback import get_latest_rss_tweet
from utils import ensure_env_exists

# ---------------------------------
# 환경 변수 체크
# ---------------------------------
if not ensure_env_exists():
    exit()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

# ---------------------------------
# 봇 로그인 이벤트
# ---------------------------------
@bot.event
async def on_ready():
    print(f"✅ 로그인 완료: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ 슬래시 명령어 {len(synced)}개 동기화 완료")
    except Exception as e:
        print(f"⚠️ 슬래시 명령어 동기화 실패: {e}")
    check_tweets.start()

# ---------------------------------
# 트윗 자동 확인 루프
# ---------------------------------
@tasks.loop(seconds=CHECK_INTERVAL)
async def check_tweets():
    print("🔄 새 트윗 확인 중...")
    try:
        has_new, tweet = await has_new_tweet()
    except RateLimitError:
        print("⚠️ 429 오류 → RSS 피드로 대체")
        tweet = await get_latest_rss_tweet()
        has_new = True if tweet else False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return

    if not has_new or not tweet:
        print("🚫 새 트윗 없음")
        return

    if not any(k in tweet["text"] for k in IMPORTANT_KEYWORDS):
        print("🟡 중요 키워드 아님 → 무시")
        return

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ 채널 ID 확인 필요")
        return

    embed = discord.Embed(
        title="📢 새로운 트윗 발견!",
        description=tweet["text"],
        color=discord.Color.blue(),
        url=tweet["url"]
    )
    embed.set_footer(text=f"출처: @{tweet['url'].split('/')[3]}")

    if tweet["media"]:
        embed.set_image(url=tweet["media"]_
