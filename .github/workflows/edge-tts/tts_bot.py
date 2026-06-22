import edge_tts
import asyncio
import os
from datetime import datetime

class TTSBot:
    def __init__(self, voice: str = "zh-TW-HsiaoChenNeural", output_dir: str = "storage/audio"):
        self.voice = voice
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    async def speak(self, script: str) -> str:
        """將文字轉為語音，回傳音檔路徑"""
        filename = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        filepath = os.path.join(self.output_dir, filename)
        
        communicate = edge_tts.Communicate(script, self.voice)
        await communicate.save(filepath)
        return filepath

    def sync_speak(self, script: str) -> str:
        """同步版本的語音合成 (供 FastAPI 呼叫)"""
        return asyncio.run(self.speak(script))

# 簡單測試
if __name__ == "__main__":
    bot = TTSBot()
    test_script = "各位觀眾晚安，歡迎收看綠能前線。今天 AI 風力預測再創佳績。"
    audio_path = bot.sync_speak(test_script)
    print(f"音檔已儲存：{audio_path}")