from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes import news, health
import os

app = FastAPI(title="Lightning AI News Global MVP", version="1.0.0")

# CORS 設定（允許前端儀表板呼叫）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(news.router)
app.include_router(health.router)

# 掛載靜態檔案（儀表板、音檔）
app.mount("/dashboard", StaticFiles(directory="dashboard", html=True), name="dashboard")
app.mount("/audio", StaticFiles(directory="storage/audio"), name="audio")

@app.get("/")
def root():
    return {"message": "Lightning AI News 已啟動，請瀏覽 /docs 查看 API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
