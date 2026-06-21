import os
import subprocess
import tempfile

# 優先使用 Edge TTS（音質最好），若無則降級至 gTTS
def speak(text):
    try:
        # 方法一：Edge TTS（推薦，免 API Key）
        import edge_tts
        import asyncio
        
        async def _speak_edge():
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_path = temp_file.name
            temp_file.close()
            
            communicate = edge_tts.Communicate(text, "zh-TW-HsiaoChenNeural")
            await communicate.save(temp_path)
            return temp_path
        
        # 取得音檔路徑
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_path = loop.run_until_complete(_speak_edge())
        loop.close()
        
        # 播放（Termux / Linux 通用）
        subprocess.run(["mpg123", "-q", audio_path], check=True)
        os.unlink(audio_path)  # 播完即刪
        return True
        
    except ImportError:
        # 降級方案：gTTS（需安裝）
        try:
            from gtts import gTTS
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_path = temp_file.name
            temp_file.close()
            
            tts = gTTS(text=text, lang="zh-TW")
            tts.save(temp_path)
            subprocess.run(["mpg123", "-q", temp_path], check=True)
            os.unlink(temp_path)
            return True
        except Exception as e:
            print(f"gTTS 錯誤：{e}")
            return False
    except Exception as e:
        print(f"Edge TTS 錯誤：{e}")
        return False
