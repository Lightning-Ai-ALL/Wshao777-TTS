
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
import io
from datetime import datetime

from db.models import Agent, LedgerEvent, AgentKpiScore
from core.kpi_engine import KPIEngine
from core.ledger import Ledger

router = APIRouter(prefix="/api/v1", tags=["Control Tower"])

# 依賴取得 DB session (沿用你原有的 get_db)
def get_db():
    # 此處需根據你實作調整
    pass

@router.post("/agents/load-csv")
async def load_agents_from_csv(
    file: UploadFile = File(...),
    mode: str = Form("replace"),  # 'replace' or 'append'
    db: Session = Depends(get_db)
):
    # 讀取 CSV 內容
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

    # 映射欄位（根據 v2 CSV 格式）
    required_cols = ["agent_id", "agent_name", "role", "capability_tags", "capability_score", "env", "status", "base_share_ratio"]
    if not all(col in df.columns for col in required_cols):
        raise HTTPException(status_code=400, detail="CSV 缺少必要欄位")

    if mode == "replace":
        db.query(Agent).delete()
        db.commit()

    loaded = 0
    for _, row in df.iterrows():
        # 檢查是否已存在（依 name 或自定義 ID）
        existing = db.query(Agent).filter(Agent.name == row["agent_name"]).first()
        if existing:
            if mode == "append":
                continue  # 跳過重複
            else:
                # replace 模式下應已刪除，此處保留安全
                pass

        agent = Agent(
            name=row["agent_name"],
            role=row["role"],
            capability_tags=row["capability_tags"],
            capability_score=row.get("capability_score", 0.0),
            env=row["env"],
            status=row["status"],
            base_share_ratio=row["base_share_ratio"]
        )
        db.add(agent)
        loaded += 1

    db.commit()
    return {"status": "success", "loaded": loaded, "mode": mode}

@router.post("/agents/start-all")
def start_all_agents(db: Session = Depends(get_db)):
    agents = db.query(Agent).filter(Agent.status == "ACTIVE_AGENT").all()
    total = len(agents)
    failed = 0
    for agent in agents:
        try:
            # 實際啟動邏輯（例如註冊到排程器或變更狀態）
            agent.env = "PROD"  # 示範更新
            # 此處可加入實際啟動任務的呼叫
            db.commit()
        except Exception:
            failed += 1
    return {"status": "started", "total": total, "failed": failed}

@router.get("/agents", response_model=dict)
def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Agent)
    if role:
        query = query.filter(Agent.role == role)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [{
            "id": a.id,
            "name": a.name,
            "role": a.role,
            "capability_tags": a.capability_tags,
            "env": a.env,
            "status": a.status,
            "base_share_ratio": a.base_share_ratio
        } for a in items]
    }

@router.get("/agents/{agent_id}", response_model=dict)
def get_agent_detail(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    # 計算總分潤 (從 ledger_events 加總)
    total_balance = db.query(func.sum(LedgerEvent.final_share)).filter(LedgerEvent.agent_id == agent_id).scalar() or 0.0
    return {
        "id": agent.id,
        "name": agent.name,
        "role": agent.role,
        "capability_tags": agent.capability_tags,
        "capability_score": agent.capability_score,
        "env": agent.env,
        "status": agent.status,
        "base_share_ratio": agent.base_share_ratio,
        "total_balance": total_balance
    }

@router.get("/ledger/realtime", response_model=dict)
def get_realtime_ledger(
    role: Optional[str] = None,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(
        Agent.id, Agent.name, func.sum(LedgerEvent.final_share).label("total_share")
    ).join(LedgerEvent, Agent.id == LedgerEvent.agent_id).group_by(Agent.id)
    if role:
        query = query.filter(Agent.role == role)
    if agent_id:
        query = query.filter(Agent.id == agent_id)
    results = query.all()
    total_revenue = sum(r.total_share for r in results if r.total_share)
    items = [{"agent_id": r.id, "name": r.name, "final_share": r.total_share or 0.0} for r in results]
    return {"total_revenue": total_revenue, "items": items}

@router.get("/kpi/dashboard", response_model=dict)
def get_kpi_dashboard(
    period: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if period is None:
        now = datetime.utcnow()
        period = f"{now.year}-Q{(now.month-1)//3 + 1}"

    # 計算本季所有 Agent 的綜合 KPI 分數（從 agent_kpi_scores 表聚合）
    # 此處假設已預先計算存檔，若無則即時計算（但較耗時）
    # 示範：取得各 Agent 該季的平均得分
    scores = db.query(
        AgentKpiScore.agent_id,
        func.avg(AgentKpiScore.score).label("avg_score")
    ).filter(AgentKpiScore.period == period).group_by(AgentKpiScore.agent_id).all()

    if not scores:
        return {"period": period, "avg_kpi": 1.0, "top_agent": None, "bottom_agent": None, "kpi_distribution": {}}

    avg_all = sum(s.avg_score for s in scores) / len(scores)
    top = max(scores, key=lambda x: x.avg_score)
    bottom = min(scores, key=lambda x: x.avg_score)

    # 分布統計（分數區間）
    bins = [0.8, 0.9, 1.0, 1.05, 1.15]
    labels = ['0.8-0.9', '0.9-1.0', '1.0-1.05', '1.05-1.15']
    dist = {label: 0 for label in labels}
    for s in scores:
        for i, (low, high) in enumerate(zip(bins, bins[1:])):
            if low <= s.avg_score < high:
                dist[labels[i]] += 1
                break
    total = len(scores)
    kpi_distribution = {k: round(v/total, 2) for k, v in dist.items()}

    return {
        "period": period,
        "avg_kpi": round(avg_all, 4),
        "top_agent": {"agent_id": top.agent_id, "score": top.avg_score},
        "bottom_agent": {"agent_id": bottom.agent_id, "score": bottom.avg_score},
        "kpi_distribution": kpi_distribution
    }
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
import io
from datetime import datetime

from db.models import Agent, LedgerEvent, AgentKpiScore
from core.kpi_engine import KPIEngine
from core.ledger import Ledger

router = APIRouter(prefix="/api/v1", tags=["Control Tower"])

# 依賴取得 DB session (沿用你原有的 get_db)
def get_db():
    # 此處需根據你實作調整
    pass

@router.post("/agents/load-csv")
async def load_agents_from_csv(
    file: UploadFile = File(...),
    mode: str = Form("replace"),  # 'replace' or 'append'
    db: Session = Depends(get_db)
):
    # 讀取 CSV 內容
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

    # 映射欄位（根據 v2 CSV 格式）
    required_cols = ["agent_id", "agent_name", "role", "capability_tags", "capability_score", "env", "status", "base_share_ratio"]
    if not all(col in df.columns for col in required_cols):
        raise HTTPException(status_code=400, detail="CSV 缺少必要欄位")

    if mode == "replace":
        db.query(Agent).delete()
        db.commit()

    loaded = 0
    for _, row in df.iterrows():
        # 檢查是否已存在（依 name 或自定義 ID）
        existing = db.query(Agent).filter(Agent.name == row["agent_name"]).first()
        if existing:
            if mode == "append":
                continue  # 跳過重複
            else:
                # replace 模式下應已刪除，此處保留安全
                pass

        agent = Agent(
            name=row["agent_name"],
            role=row["role"],
            capability_tags=row["capability_tags"],
            capability_score=row.get("capability_score", 0.0),
            env=row["env"],
            status=row["status"],
            base_share_ratio=row["base_share_ratio"]
        )
        db.add(agent)
        loaded += 1

    db.commit()
    return {"status": "success", "loaded": loaded, "mode": mode}

@router.post("/agents/start-all")
def start_all_agents(db: Session = Depends(get_db)):
    agents = db.query(Agent).filter(Agent.status == "ACTIVE_AGENT").all()
    total = len(agents)
    failed = 0
    for agent in agents:
        try:
            # 實際啟動邏輯（例如註冊到排程器或變更狀態）
            agent.env = "PROD"  # 示範更新
            # 此處可加入實際啟動任務的呼叫
            db.commit()
        except Exception:
            failed += 1
    return {"status": "started", "total": total, "failed": failed}

@router.get("/agents", response_model=dict)
def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Agent)
    if role:
        query = query.filter(Agent.role == role)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [{
            "id": a.id,
            "name": a.name,
            "role": a.role,
            "capability_tags": a.capability_tags,
            "env": a.env,
            "status": a.status,
            "base_share_ratio": a.base_share_ratio
        } for a in items]
    }

@router.get("/agents/{agent_id}", response_model=dict)
def get_agent_detail(agent_id: int, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    # 計算總分潤 (從 ledger_events 加總)
    total_balance = db.query(func.sum(LedgerEvent.final_share)).filter(LedgerEvent.agent_id == agent_id).scalar() or 0.0
    return {
        "id": agent.id,
        "name": agent.name,
        "role": agent.role,
        "capability_tags": agent.capability_tags,
        "capability_score": agent.capability_score,
        "env": agent.env,
        "status": agent.status,
        "base_share_ratio": agent.base_share_ratio,
        "total_balance": total_balance
    }

@router.get("/ledger/realtime", response_model=dict)
def get_realtime_ledger(
    role: Optional[str] = None,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(
        Agent.id, Agent.name, func.sum(LedgerEvent.final_share).label("total_share")
    ).join(LedgerEvent, Agent.id == LedgerEvent.agent_id).group_by(Agent.id)
    if role:
        query = query.filter(Agent.role == role)
    if agent_id:
        query = query.filter(Agent.id == agent_id)
    results = query.all()
    total_revenue = sum(r.total_share for r in results if r.total_share)
    items = [{"agent_id": r.id, "name": r.name, "final_share": r.total_share or 0.0} for r in results]
    return {"total_revenue": total_revenue, "items": items}

@router.get("/kpi/dashboard", response_model=dict)
def get_kpi_dashboard(
    period: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if period is None:
        now = datetime.utcnow()
        period = f"{now.year}-Q{(now.month-1)//3 + 1}"

    # 計算本季所有 Agent 的綜合 KPI 分數（從 agent_kpi_scores 表聚合）
    # 此處假設已預先計算存檔，若無則即時計算（但較耗時）
    # 示範：取得各 Agent 該季的平均得分
    scores = db.query(
        AgentKpiScore.agent_id,
        func.avg(AgentKpiScore.score).label("avg_score")
    ).filter(AgentKpiScore.period == period).group_by(AgentKpiScore.agent_id).all()

    if not scores:
        return {"period": period, "avg_kpi": 1.0, "top_agent": None, "bottom_agent": None, "kpi_distribution": {}}

    avg_all = sum(s.avg_score for s in scores) / len(scores)
    top = max(scores, key=lambda x: x.avg_score)
    bottom = min(scores, key=lambda x: x.avg_score)

    # 分布統計（分數區間）
    bins = [0.8, 0.9, 1.0, 1.05, 1.15]
    labels = ['0.8-0.9', '0.9-1.0', '1.0-1.05', '1.05-1.15']
    dist = {label: 0 for label in labels}
    for s in scores:
        for i, (low, high) in enumerate(zip(bins, bins[1:])):
            if low <= s.avg_score < high:
                dist[labels[i]] += 1
                break
    total = len(scores)
    kpi_distribution = {k: round(v/total, 2) for k, v in dist.items()}

    return {
        "period": period,
        "avg_kpi": round(avg_all, 4),
        "top_agent": {"agent_id": top.agent_id, "score": top.avg_score},
        "bottom_agent": {"agent_id": bottom.agent_id, "score": bottom.avg_score},
        "kpi_distribution": kpi_distribution
    }