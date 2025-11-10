import aiohttp
from datetime import datetime
from config import USERNAME, RSS_FEED_URL

async def get_latest_rss_tweet():
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 🌐 RSS 피드에서 최신 트윗 확인 중...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(RSS_FEED_URL, timeout=15) as resp:
                if resp.status != 200:
                    print(f"❌ RSS 요청 실패: {resp.status}")
                    return None
                data = await resp.json()
    except Exception as e:
        print(f"⚠️ RSS 요청 중 오류 발생: {e}")
        return None
    items = data.get("items", [])
    if not items:
        print("❌ RSS 피드에 트윗 항목이 없습니다.")
        return None
    latest = items[0]
    tweet_url = latest.get("url", "")
    tweet_id = tweet_url.split("/")[-1] if "/status/" in tweet_url else str(hash(tweet_url))
    tweet_text = latest.get("title", "").strip() or latest.get("description", "").strip()
    media_urls = []
    if "media" in latest and isinstance(latest["media"], list):
        for m in latest["media"]:
            if isinstance(m, str) and m.lower().startswith("http"):
                media_urls.append(m)
    content_html = latest.get("content_html", "")
    if not media_urls and "<img" in content_html:
        import re
        media_urls = re.findall(r'<img[^>]+src="([^"]+)"', content_html)
    tweet = {
        "id": tweet_id,
        "text": tweet_text,
        "created_at": latest.get("date_published", datetime.now().isoformat()),
        "url": tweet_url,
        "media": media_urls,
    }
    print(f"✅ RSS로 대체 트윗 로드 완료: {tweet['url']}")
    return tweet
