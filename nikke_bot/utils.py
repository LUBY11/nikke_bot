import os

def ensure_env_exists():
    if not os.path.exists(".env"):
        print("⚙️  .env 파일이 없습니다. 기본 템플릿을 생성합니다.")
        with open(".env", "w", encoding="utf-8") as f:
            f.write(
                "DISCORD_TOKEN=\n"
                "CHANNEL_ID=\n"
                "TWITTER_BEARER_TOKEN=\n"
                "TWITTER_USERNAME=NIKKE_kr\n"
                "RSS_FEED_URL=https://rss.app/feeds/v1.1/MTI3E57SlYF7BAgl.json\n"
            )
        print("✅ .env 파일이 생성되었습니다. 값을 입력 후 다시 실행하세요.")
        return False
    return True
