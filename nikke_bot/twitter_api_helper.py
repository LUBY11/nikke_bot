import aiohttp
import re
from datetime import datetime
from config import BEARER_TOKEN, USERNAME, API_BASE

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "User-Agent": "NikkeDiscordBot/1.1"
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
        "tweet.fields": "created_at,entities,attachments",
        "expansions": "attachments.media_keys",
        "media.fields": "url,preview_image_url"
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
        text = tweet["text"]
        created_at = tweet.get("created_at")
        tweet_id = tweet["id"]
        includes = data.get("includes", {}).get("media", [])
        media_urls = []
        for media in includes:
            if "url" in media:
                media_urls.append(media["url"])
            elif "preview_image_url" in media:
                media_urls.append(media["preview_image_url"])
        inline_media = re.findall(r"(https?://\S+\.(?:jpg|jpeg|png|gif))", text)
        media_urls.extend(inline_media)
        media_urls = list(dict.fromkeys(media_urls))
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
