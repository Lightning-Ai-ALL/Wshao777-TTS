# 1. 安裝依賴
pip install -r requirements.txt

# 2. 設定環境變數（可選，若無則使用模板）
cp .env.example .env
# 編輯 .env 填入 GEMINI_API_KEY（若無則略過）

# 3. 啟動服務
python app.py
# 或 uvicorn app:app --reload

# 4. 開啟儀表板
# 瀏覽器訪問 http://127.0.0.1:8000/dashboard