from db.models import LedgerEntry, AgentRegistry
from sqlalchemy.orm import sessionmaker

class Ledger:
    def __init__(self, db_session):
        self.session = db_session

    def record_event(self, agent_name, event_type, amount=0.0, metadata=None):
        # 1. 查詢 Agent 基礎分潤比例
        agent = self.session.query(AgentRegistry).filter_by(name=agent_name).first()
        if not agent:
            raise ValueError(f"Agent {agent_name} 未註冊")
        
        # 2. 計算 KPI 分數 (此處先以 stub 代替，未來串接 kpi_engine)
        kpi_score = 1.0  

        # 3. 計算最終分潤 (此處先以簡單規則代替，未來串接 reward_engine)
        final_share = amount * (agent.base_share_ratio / 100) * kpi_score

        # 4. 寫入帳本
        entry = LedgerEntry(
            agent_name=agent_name,
            event_type=event_type,
            amount=amount,
            kpi_score=kpi_score,
            final_share=final_share,
            metadata=metadata
        )
        self.session.add(entry)
        self.session.commit()
        return entry

    def get_balance(self, agent_name):
        # 查詢某 Agent 的累計分潤
        entries = self.session.query(LedgerEntry).filter_by(agent_name=agent_name).all()
        return sum(e.final_share for e in entries)