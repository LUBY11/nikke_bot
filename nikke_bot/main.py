import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime
import os
from dotenv import load_dotenv

from twitter_api_helper import has_new_tweet, RateLimitError, get_latest_tweet
from rss_fallback import get_latest_rss_tweet


# -------------------------------------
# .env 자동 생성 및 로드
# -------------------------------------
def ensure_env():
    """자동 .env 생성 (없을 시 안내 후 종료)"""
    if not os.path.exists(".env"):
        print("🚀 최초 실행 감지! .env 파일을 자동 생성합니다.\n")
        content = (
            "# ⚠️ 자동 생성된 환경 파일입니다. 아래 값들을 채워주세요.\n"
            "DISCORD_TOKEN=\n"
            "DISCORD_CHANNEL_ID=\n"
            "TWITTER_BEARER_TOKEN=\n"
            "USERNAME=NIKKE_kr\n"
            "IMPORTANT_KEYWORDS=점검,업데이트,이벤트,긴급\n"
            "RSS_FALLBACK_URL=https://nitter.net/NIKKE_kr/rss\n"
        )
        with open(".env", "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ .env 생성 완료! 필요한 토큰 정보를 입력한 뒤 다시 실행하세요.")
        exit(0)


ensure_env()
load_dotenv()


# -------------------------------------
# 환경 변수 로드
# -------------------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))
USERNAME = os.getenv("USERNAME", "NIKKE_kr")
IMPORTANT_KEYWORDS = os.getenv("IMPORTANT_KEYWORDS", "업데이트,점검").split(",")
RSS_FALLBACK_URL = os.getenv("RSS_FALLBACK_URL")

# -------------------------------------
# Discord 봇 초기화
# -------------------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)
_last_sent_id = None


@bot.event
async def on_ready():
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ✅ 로그인 완료: {bot.user}")

    # ✅ 첫 실행 시 즉시 트윗 확인
    await initial_tweet_check()

    # ✅ 주기적 루프 시작 (1분마다)
    check_tweets.start()


# -------------------------------------
# 최초 1회 즉시 확인용 함수
# -------------------------------------
async def initial_tweet_check():
    global _last_sent_id
    print(f"[{datetime.now():%H:%M:%S}] 🚀 첫 실행 — 최신 트윗 확인 중...")

    try:
        has_new, tweet = await has_new_tweet(USERNAME)
    except RateLimitError:
        print("⚠️ Twitter API 제한 도달 → RSS 피드로 전환")
        tweet = await get_latest_rss_tweet()
        has_new = tweet and tweet.get("id") != _last_sent_id
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return

    if has_new and tweet:
        await send_tweet(tweet)
        _last_sent_id = tweet["id"]
    else:
        print("❌ 새 트윗 없음 — 대기 시작.")


# -------------------------------------
# 트윗 자동 확인 루프 (1분마다)
# -------------------------------------
@tasks.loop(seconds=60)
async def check_tweets():
    global _last_sent_id

    print(f"[{datetime.now():%H:%M:%S}] 🔄 새 트윗 확인 중...")

    try:
        has_new, tweet = await has_new_tweet(USERNAME)
    except RateLimitError:
        print("⚠️ API 제한 — RSS 피드로 우회")
        tweet = await get_latest_rss_tweet()
        has_new = tweet and tweet.get("id") != _last_sent_id
    except Exception as e:
        print(f"⚠️ 오류 발생: {e}")
        return

    if has_new and tweet:
        if tweet["id"] == _last_sent_id:
            print("⏩ 이미 전송된 트윗 — 패스")
            return

        await send_tweet(tweet)
        _last_sent_id = tweet["id"]
    else:
        print("❌ 새 트윗 없음.")


# -------------------------------------
# 트윗 임베드 전송
# -------------------------------------
async def send_tweet(tweet):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ 채널을 찾을 수 없습니다.")
        return

    text = tweet["text"]
    highlighted = any(k in text for k in IMPORTANT_KEYWORDS)

    if highlighted:
        await channel.send("@everyone 🚨 **중요 트윗 감지됨!** 🚨")

    embed = discord.Embed(
        title=f"🕊️ @{USERNAME} 새 트윗{' ‼️' if highlighted else ''}",
        description=text,
        url=tweet["url"],
        color=discord.Color.red() if highlighted else discord.Color.blue(),
        timestamp=datetime.now(),
    )

    embed.set_footer(text=f"작성 시각: {tweet.get('created_at', '알 수 없음')}")

    if tweet.get("media"):
        for i, media_url in enumerate(tweet["media"]):
            if i == 0:
                embed.set_image(url=media_url)
            else:
                await channel.send(media_url)

    await channel.send(embed=embed)
    print(f"[{datetime.now():%H:%M:%S}] ✅ 새 트윗 전송 완료: {tweet['url']}")


# -------------------------------------
# /check 명령
# -------------------------------------
@bot.tree.command(name="check", description="최신 트윗 수동 확인")
async def check(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    try:
        tweet = await get_latest_tweet(USERNAME)
    except RateLimitError:
        print("⚠️ API 제한. RSS로 대체합니다.")
        tweet = await get_latest_rss_tweet()

    if not tweet:
        await interaction.followup.send("❌ 트윗을 가져올 수 없습니다.")
        return

    await send_tweet(tweet)
    await interaction.followup.send("✅ 최신 트윗을 불러왔습니다.")


# -------------------------------------
# 안전한 실행
# -------------------------------------
def main_cli():
    try:
        bot.run(TOKEN)
    except KeyboardInterrupt:
        print("🛑 수동 종료됨")


if __name__ == "__main__":
    main_cli()
