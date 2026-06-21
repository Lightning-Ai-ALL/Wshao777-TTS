from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.ledger import Ledger
from db.models import Base

app = FastAPI(title="Lightning Control Tower")

# 資料庫連線 (此處使用 SQLite，可輕鬆換成 PostgreSQL)
DATABASE_URL = "sqlite:///./lightning.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立表格
Base.metadata.create_all(bind=engine)

# 依賴項：取得資料庫 Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Lightning Control Tower is running"}

@app.post("/api/ledger/record")
def record_event(agent_name: str, event_type: str, amount: float, db=Depends(get_db)):
    ledger = Ledger(db)
    entry = ledger.record_event(agent_name, event_type, amount)
    return {"status": "recorded", "entry_id": entry.id}

@app.get("/api/ledger/balance/{agent_name}")
def get_balance(agent_name: str, db=Depends(get_db)):
    ledger = Ledger(db)
    balance = ledger.get_balance(agent_name)
    return {"agent": agent_name, "balance": balance}