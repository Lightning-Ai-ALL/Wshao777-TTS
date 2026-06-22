from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import news
import os
from dotenv import load_dotenv

load_dotenv()  # 載入 .env 中的 API Keys

app = FastAPI(title="Lightning AI News 188 Control Tower", version="0.1.0")

# 允許 CORS (方便未來 Dashboard 串接)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(news.router)

@app.get("/")
async def root():
    return {"message": "Lightning AI News Control Tower is running", "docs": "/docs"}

# 若直接執行此檔案，啟動 uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)