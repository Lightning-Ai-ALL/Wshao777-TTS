import os
import google.generativeai as genai
from typing import List, Dict

class AnchorBot:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def generate_script(self, news_list: List[Dict]) -> str:
        if self.model:
            return self._generate_with_gemini(news_list)
        else:
            return self._generate_with_template(news_list)

    def _generate_with_gemini(self, news_list: List[Dict]) -> str:
        news_text = "\n".join([f"標題：{n['headline']}\n摘要：{n['summary']}" for n in news_list])
        prompt = f"""
        你是一位專業的綠能新聞主播，請根據以下新聞內容，撰寫一則 60 秒的新聞播報稿。
        語氣要沉穩專業，開頭為「各位觀眾晚安，歡迎收看綠能前線」。
        新聞內容：
        {news_text}
        請直接輸出主播稿，不要附加任何評論。
        """
        response = self.model.generate_content(prompt)
        return response.text

    def _generate_with_template(self, news_list: List[Dict]) -> str:
        headlines = "、".join([n['headline'] for n in news_list])
        return f"""
        各位觀眾晚安，歡迎收看綠能前線。
        今天為您報導的重點新聞包括：{headlines}。
        詳細內容請鎖定本台後續報導。
        我是主播，我們下次見。
        """

if __name__ == "__main__":
    sample_news = [{"headline": "測試新聞", "summary": "這是一則測試摘要"}]
    bot = AnchorBot()
    print(bot.generate_script(sample_news))
latest_broadcast.json