from sqlalchemy.orm import Session
from db.models import Agent, KpiDefinition, AgentKpiScore
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class KPIEngine:
    def __init__(self, db_session: Session):
        self.session = db_session

    def get_applicable_kpis(self, agent: Agent) -> List[KpiDefinition]:
        """根據 Agent 的角色，篩選適用的 KPI 定義"""
        roles = agent.role.split(',')  # 若角色有多個，以逗號分隔
        query = self.session.query(KpiDefinition)
        # 若 applicable_roles 為 NULL 或空字串，則視為通用
        applicable = []
        for kpi in query.all():
            if not kpi.applicable_roles or kpi.applicable_roles.strip() == '':
                applicable.append(kpi)
            else:
                kpi_roles = [r.strip() for r in kpi.applicable_roles.split(',')]
                if any(role in kpi_roles for role in roles):
                    applicable.append(kpi)
        return applicable

    def compute_kpi_score(self, agent: Agent, period: str, actual_values: Dict[str, float]) -> float:
        """
        計算某 Agent 在某一季的綜合 KPI 分數
        :param agent: Agent 物件
        :param period: 季度字串，如 '2026-Q2'
        :param actual_values: 各 KPI 名稱對應的實際值，如 {'data_accuracy': 97.5, 'task_volume': 120}
        :return: 綜合分數 (0.8 ~ 1.15)
        """
        kpis = self.get_applicable_kpis(agent)
        total_weight = 0.0
        weighted_score = 0.0

        for kpi in kpis:
            actual = actual_values.get(kpi.name)
            if actual is None:
                logger.warning(f"Agent {agent.name} 缺少 KPI {kpi.name} 的實際值，跳過")
                continue

            # 計算該 KPI 的單項分數（線性映射）
            if kpi.target_value > 0:
                ratio = actual / kpi.target_value
            else:
                ratio = 1.0  # 若目標值為 0，視為滿分

            # 分數範圍限制：0.8 ~ 1.15
            single_score = max(0.8, min(1.15, ratio))
            weighted_score += single_score * kpi.weight
            total_weight += kpi.weight

        # 若沒有適用的 KPI，回傳 1.0（基準值）
        if total_weight == 0:
            return 1.0

        final_score = weighted_score / total_weight
        # 確保最終分數落在 0.8~1.15 之間
        return round(max(0.8, min(1.15, final_score)), 4)

    def save_kpi_scores(self, agent_id: int, period: str, actual_values: Dict[str, float]):
        """將計算出的各項 KPI 分數存入 agent_kpi_scores 表（可選）"""
        agent = self.session.query(Agent).filter_by(id=agent_id).first()
        if not agent:
            raise ValueError(f"Agent ID {agent_id} 不存在")

        kpis = self.get_applicable_kpis(agent)
        for kpi in kpis:
            actual = actual_values.get(kpi.name)
            if actual is None:
                continue
            # 計算單項分數
            if kpi.target_value > 0:
                ratio = actual / kpi.target_value
            else:
                ratio = 1.0
            single_score = max(0.8, min(1.15, ratio))
            # 存入或更新
            record = self.session.query(AgentKpiScore).filter_by(
                agent_id=agent_id, period=period, kpi_id=kpi.id
            ).first()
            if record:
                record.actual_value = actual
                record.score = single_score
            else:
                record = AgentKpiScore(
                    agent_id=agent_id,
                    period=period,
                    kpi_id=kpi.id,
                    actual_value=actual,
                    score=single_score
                )
                self.session.add(record)
        self.session.commit()