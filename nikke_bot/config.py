import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
RSS_FEED_URL = os.getenv("RSS_FEED_URL", "https://rss.app/feeds/v1.1/MTI3E57SlYF7BAgl.json")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
USERNAME = os.getenv("TWITTER_USERNAME", "NIKKE_kr")
API_BASE = "https://api.twitter.com/2"

IMPORTANT_KEYWORDS = [
    "솔로 레이드", "협동작전", "업데이트", "점검", "이벤트", "긴급"
]
CHECK_INTERVAL = 600  # 초 단위 (10분)
LAST_ID_FILE = "last_id.txt"
