from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from agents.news_bot import NewsBot
from agents.anchor_bot import AnchorBot
from agents.tts_bot import TTSBot

router = APIRouter(prefix="/news", tags=["News Pipeline"])

# 簡單的記憶體儲存 Pipeline 狀態 (正式應用應改用資料庫)
pipeline_store = {}

class PipelineStatus(BaseModel):
    pipeline_id: str
    status: str  # pending, running, completed, failed
    progress: float  # 0.0 ~ 1.0
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str

def run_news_pipeline_task(pipeline_id: str, rss_url: str = None):
    """背景執行新聞產製流程"""
    try:
        # 1. 更新狀態：執行中
        pipeline_store[pipeline_id]["status"] = "running"
        pipeline_store[pipeline_id]["progress"] = 0.2
        pipeline_store[pipeline_id]["updated_at"] = datetime.now().isoformat()

        # 2. NewsBot 抓取
        news_bot = NewsBot(rss_url=rss_url) if rss_url else NewsBot()
        news_list = news_bot.fetch_latest(limit=3)
        pipeline_store[pipeline_id]["progress"] = 0.5

        # 3. AnchorBot 生成主播稿
        anchor_bot = AnchorBot()
        script = anchor_bot.generate_script(news_list)
        pipeline_store[pipeline_id]["progress"] = 0.75

        # 4. TTSBot 語音合成
        tts_bot = TTSBot()
        audio_path = tts_bot.sync_speak(script)
        pipeline_store[pipeline_id]["progress"] = 1.0

        # 5. 儲存結果
        pipeline_store[pipeline_id]["status"] = "completed"
        pipeline_store[pipeline_id]["result"] = {
            "news_count": len(news_list),
            "script": script,
            "audio_path": audio_path,
            "headlines": [n["headline"] for n in news_list]
        }
        pipeline_store[pipeline_id]["updated_at"] = datetime.now().isoformat()

    except Exception as e:
        pipeline_store[pipeline_id]["status"] = "failed"
        pipeline_store[pipeline_id]["error"] = str(e)
        pipeline_store[pipeline_id]["updated_at"] = datetime.now().isoformat()

@router.post("/run-pipeline")
async def run_pipeline(background_tasks: BackgroundTasks, rss_url: Optional[str] = None):
    """啟動一次完整的新聞產製流程"""
    pipeline_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    pipeline_store[pipeline_id] = {
        "pipeline_id": pipeline_id,
        "status": "pending",
        "progress": 0.0,
        "result": None,
        "error": None,
        "created_at": now,
        "updated_at": now
    }
    # 在背景執行
    background_tasks.add_task(run_news_pipeline_task, pipeline_id, rss_url)
    
    return {"pipeline_id": pipeline_id, "status": "pending", "message": "Pipeline started"}

@router.get("/pipeline-status/{pipeline_id}")
async def get_pipeline_status(pipeline_id: str):
    """查詢特定 Pipeline 的執行狀態"""
    status = pipeline_store.get(pipeline_id)
    if not status:
        raise HTTPException(status_code=404, detail="Pipeline ID not found")
    return status

@router.get("/latest-broadcast")
async def get_latest_broadcast():
    """取得最新一則已完成的播報 (示範功能)"""
    # 實務上應從資料庫查詢最新一筆 completed 記錄
    completed = [p for p in pipeline_store.values() if p["status"] == "completed"]
    if not completed:
        return {"message": "尚無已完成的新聞播報"}
    latest = sorted(completed, key=lambda x: x["updated_at"], reverse=True)[0]
    return latest