from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from db.models import Agent, LedgerEvent  # 這裡需定義對應的 SQLAlchemy ORM 類別

app = FastAPI()
DATABASE_URL = "sqlite:///./ledger.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# 依賴注入
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 查詢所有 Agent (分頁)
@app.get("/api/agents")
def list_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    agents = db.query(Agent).offset(skip).limit(limit).all()
    return agents

# 查詢特定 Agent 的累計分潤 (從 ledger_events 加總)
@app.get("/api/agents/{agent_id}/balance")
def get_agent_balance(agent_id: int, db: Session = Depends(get_db)):
    total = db.query(func.sum(LedgerEvent.final_share)).filter(LedgerEvent.agent_id == agent_id).scalar()
    return {"agent_id": agent_id, "total_balance": total or 0.0}

# 記錄事件 (對應 ledger.record_event)
@app.post("/api/ledger/record")
def record_event(agent_id: int, event_type: str, amount: float, metadata: str = None, db: Session = Depends(get_db)):
    # 這裡可以加入 KPI 引擎計算 kpi_score 與 final_share
    # 簡單範例：假設 kpi_score = 1.0
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    kpi_score = 1.0
    final_share = amount * (agent.base_share_ratio / 100) * kpi_score
    
    event = LedgerEvent(
        agent_id=agent_id,
        event_type=event_type,
        amount=amount,
        kpi_score=kpi_score,
        final_share=final_share,
        metadata=metadata
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"status": "recorded", "event_id": event.id}