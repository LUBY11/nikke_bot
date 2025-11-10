import aiohttp
from datetime import datetime
from config import BEARER_TOKEN, USERNAME, API_BASE

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "User-Agent": "NikkeDiscordBot/1.2"
}

_last_seen = None

class RateLimitError(Exception):
    pass


async def get_user_id(session, username):
    url = f"{API_BASE}/users/by/username/{username}"
    async with session.get(url, headers=HEADERS) as resp:
        if resp.status == 429:
            raise RateLimitError("Too Many Requests (429)")
        if resp.status != 200:
            text = await resp.text()
            raise RuntimeError(f"get_user_id 실패 {resp.status}: {text}")
        data = await resp.json()
        return data.get("data", {}).get("id")


async def fetch_tweets(session, user_id):
    url = f"{API_BASE}/users/{user_id}/tweets"
    params = {
        "exclude": "replies,retweets",
        "max_results": "5",
        "tweet.fields": "created_at,attachments",
        "expansions": "attachments.media_keys",
        "media.fields": "url,preview_image_url,type"
    }
    async with session.get(url, headers=HEADERS, params=params) as resp:
        if resp.status == 429:
            raise RateLimitError("Too Many Requests (429)")
        if resp.status != 200:
            text = await resp.text()
            raise RuntimeError(f"fetch_tweets 실패 {resp.status}: {text}")
        return await resp.json()


async def get_latest_tweet(username=USERNAME):
    async with aiohttp.ClientSession() as session:
        user_id = await get_user_id(session, username)
        if not user_id:
            print("❌ 사용자 ID 불러오기 실패")
            return None

        data = await fetch_tweets(session, user_id)
        tweets = data.get("data") or []
        if not tweets:
            print("❌ 트윗 없음")
            return None

        tweet = tweets[0]
        tweet_id = tweet["id"]
        text = tweet["text"]
        created_at = tweet.get("created_at")

        # ✅ 트윗에 실제 연결된 media만 추출
        media_urls = []
        media_keys = tweet.get("attachments", {}).get("media_keys", [])
        includes_media = data.get("includes", {}).get("media", [])

        for media in includes_media:
            if media.get("media_key") in media_keys:
                url = media.get("url") or media.get("preview_image_url")
                if url:
                    media_urls.append(url)

        return {
            "id": tweet_id,
            "text": text,
            "created_at": created_at,
            "url": f"https://x.com/{username}/status/{tweet_id}",
            "media": media_urls,
        }


async def has_new_tweet(username=USERNAME):
    global _last_seen
    tweet = await get_latest_tweet(username)
    if not tweet:
        return False, None

    if _last_seen != tweet["id"]:
        _last_seen = tweet["id"]
        print(f"🆕 새 트윗 발견! ID={_last_seen}")
        return True, tweet
    return False, None
