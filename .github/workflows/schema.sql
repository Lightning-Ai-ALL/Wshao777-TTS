-- ----------------------------
-- 1. Agent 註冊表 (存放所有 AI/BOT 的基本資訊)
-- ----------------------------
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- SQLite 版；PostgreSQL 用 SERIAL
    name VARCHAR(100) UNIQUE NOT NULL,
    capability_tags VARCHAR(255),          -- 逗號分隔的能力標籤 (如 "風力演練,數據審計")
    role VARCHAR(50) NOT NULL,             -- 技術核心 / 數據管理 / 治理安全 / 支援運營 / 投資方
    base_share_ratio DECIMAL(5,4) NOT NULL DEFAULT 0.0,  -- 基礎分潤比例 (如 2.5000%)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------
-- 2. 帳本事件表 (記錄每一筆收入/貢獻事件)
-- ----------------------------
CREATE TABLE IF NOT EXISTS ledger_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,             -- 關聯 agents.id
    event_type VARCHAR(50) NOT NULL,       -- 'task_complete', 'api_call', 'data_processed', 'subscription'
    amount DECIMAL(15,2) DEFAULT 0.0,      -- 該事件產生的收益金額 (或成本，以正負表示)
    kpi_score DECIMAL(3,2) DEFAULT 1.0,    -- 該事件對應的 KPI 達成率 (0.80 ~ 1.15)
    final_share DECIMAL(15,4) DEFAULT 0.0, -- 最終計算出的分潤 (已乘 base_share_ratio * kpi_score)
    metadata TEXT,                         -- JSON 格式的額外資訊 (如任務ID、請求參數)
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- ----------------------------
-- 3. KPI 定義表 (可彈性擴充 KPI 項目)
-- ----------------------------
CREATE TABLE IF NOT EXISTS kpi_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,     -- 如 'data_accuracy', 'task_volume'
    description TEXT,
    target_value DECIMAL(10,4),            -- 目標值 (如 95.0000 代表 95%)
    weight DECIMAL(3,2) DEFAULT 1.0,       -- 權重 (用於綜合評分)
    applicable_roles VARCHAR(255)          -- 適用的角色，逗號分隔；若空則全部適用
);

-- ----------------------------
-- 4. Agent 季度 KPI 成績表 (記錄每季度的 KPI 達成情況)
-- ----------------------------
CREATE TABLE IF NOT EXISTS agent_kpi_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    period VARCHAR(20) NOT NULL,           -- 如 '2026-Q2'
    kpi_id INTEGER NOT NULL,
    actual_value DECIMAL(10,4),            -- 實際值
    score DECIMAL(3,2) DEFAULT 1.0,        -- 轉換後的分數 (0.8~1.15)
    notes TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (kpi_id) REFERENCES kpi_definitions(id) ON DELETE CASCADE,
    UNIQUE(agent_id, period, kpi_id)
);

-- ----------------------------
-- 索引 (加速查詢)
-- ----------------------------
CREATE INDEX idx_ledger_agent_id ON ledger_events(agent_id);
CREATE INDEX idx_ledger_occurred_at ON ledger_events(occurred_at);
CREATE INDEX idx_agent_kpi_agent_period ON agent_kpi_scores(agent_id, period);