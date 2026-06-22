import asyncio
import json
import sys
from datetime import datetime
from agents.news_bot import NewsBot
from agents.anchor_bot import AnchorBot
from agents.tts_bot import TTSBot

async def main():
    print(f"🚀 [{datetime.now()}] 啟動新聞產製 Pipeline...")
    try:
        # 1. NewsBot
        print("📰 正在抓取新聞...")
        news_bot = NewsBot()
        news_list = news_bot.fetch_latest(limit=3)
        print(f"✅ 抓到 {len(news_list)} 則新聞")

        # 2. AnchorBot
        print("✍️ 正在生成主播稿...")
        anchor_bot = AnchorBot()
        script = anchor_bot.generate_script(news_list)
        print(f"✅ 主播稿已完成 ({len(script)} 字)")

        # 3. TTSBot
        print("🗣️ 正在合成語音...")
        tts_bot = TTSBot()
        audio_path = tts_bot.sync_speak(script)
        print(f"✅ 語音已儲存：{audio_path}")

        # 4. 儲存結果
        result = {
            "timestamp": datetime.now().isoformat(),
            "headlines": [n["headline"] for n in news_list],
            "script": script,
            "audio_path": audio_path,
            "status": "completed"
        }
        os.makedirs("storage", exist_ok=True)
        with open("storage/latest_broadcast.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print("✅ 新聞產製 Pipeline 全部完成！")
        print(f"📊 查看結果：storage/latest_broadcast.json")
        print(f"🎧 收聽播報：{audio_path}")
        return True
    except Exception as e:
        print(f"❌ Pipeline 失敗：{e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)