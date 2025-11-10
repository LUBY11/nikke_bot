import os
import asyncio
import discord
from discord.ext import tasks
from config import TOKEN, CHANNEL_ID, CHECK_INTERVAL, IMPORTANT_KEYWORDS
from twitter_api_helper import has_new_tweet, RateLimitError
from rss_fallback import get_latest_rss_tweet
from utils import ensure_env_exists

if not ensure_env_exists():
    exit()

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ 로그인 완료: {client.user}")
    check_tweets.start()

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
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ 채널 ID 확인 필요")
        return
    embed = discord.Embed(title="📢 새로운 트윗 발견!", description=tweet["text"], color=discord.Color.blue(), url=tweet["url"])
    embed.set_footer(text=f"출처: @{tweet['url'].split('/')[3]}")
    if tweet["media"]:
        embed.set_image(url=tweet["media"][0])
    await channel.send(embed=embed)
    print(f"✅ 전송 완료: {tweet['url']}")

def main():
    if not TOKEN:
        print("❌ DISCORD_TOKEN이 .env에 없습니다.")
        return
    client.run(TOKEN)

if __name__ == "__main__":
    main()
