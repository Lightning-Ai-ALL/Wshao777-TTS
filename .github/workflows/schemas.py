from pydantic import BaseModel
from typing import Optional, List

class AgentResponse(BaseModel):
    id: int
    name: str
    role: str
    capability_tags: str
    capability_score: Optional[float] = None
    env: str
    status: str
    base_share_ratio: float

class AgentDetailResponse(AgentResponse):
    total_balance: float

class LedgerItem(BaseModel):
    agent_id: int
    name: str
    final_share: float

class LedgerRealtimeResponse(BaseModel):
    total_revenue: float
    items: List[LedgerItem]

class KPIDashboardResponse(BaseModel):
    period: str
    avg_kpi: float
    top_agent: Optional[dict]
    bottom_agent: Optional[dict]
    kpi_distribution: dict