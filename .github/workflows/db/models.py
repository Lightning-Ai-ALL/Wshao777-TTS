from sqlalchemy import Column, Integer, String, Float, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class LedgerEntry(Base):
    __tablename__ = 'ledger_entries'
    id = Column(Integer, primary_key=True)
    agent_name = Column(String(100), nullable=False)
    event_type = Column(String(50), nullable=False)  # 'task_complete', 'api_call', 'data_processed'
    amount = Column(Float, default=0.0)  # 此事件產生的收益或成本
    kpi_score = Column(Float, default=1.0)  # 該事件對應的 KPI 分數
    final_share = Column(Float, default=0.0)  # 最終計算出的分潤
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(Text, nullable=True)  # JSON 格式的額外資訊

class AgentRegistry(Base):
    __tablename__ = 'agent_registry'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    capability = Column(String(200))  # 能力標籤
    role = Column(String(50))  # 技術核心/數據管理/... 
    base_share_ratio = Column(Float, default=0.0)  # 基礎分潤比例 (%)
    is_active = Column(Integer, default=1)