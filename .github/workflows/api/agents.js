async function renderAgentCards() {
    const container = document.querySelector('.grid.grid-cols-1.sm\\:grid-cols-2.lg\\:grid-cols-3.xl\\:grid-cols-4');
    if (!container) return;

    try {
        const res = await fetch('/api/v1/agents?limit=20');
        const data = await res.json();
        const agents = data.items || [];

        // 清空容器，保留最後一個「新增代理」卡片
        const addCard = container.lastElementChild;
        container.innerHTML = '';

        // 顏色循環 (7色)
        const colors = ['#FF1744', '#FF9100', '#FFEA00', '#00E676', '#00B0FF', '#2979FF', '#D500F9'];

        agents.forEach((agent, index) => {
            const color = colors[index % colors.length];
            const card = document.createElement('div');
            card.className = 'agent-card glass rounded-3xl p-5 border border-white/10 hover:border-white/20 group';
            card.style.borderLeft = `5px solid ${color}`;

            card.innerHTML = `
                <div class="flex items-start justify-between">
                    <div class="w-11 h-11 rounded-2xl flex items-center justify-center text-3xl" style="background: ${color}25; color: ${color}">
                        <i class="fa-solid fa-robot"></i>
                    </div>
                    <div class="px-3 py-1 text-[10px] font-bold rounded-xl" style="background: ${color}15; color: ${color}">
                        ${agent.env || 'v1.0'}
                    </div>
                </div>
                <div class="mt-5">
                    <div class="font-bold text-xl tracking-tight">${agent.name}</div>
                    <div class="text-white/60 text-sm mt-0.5">${agent.role} • ${agent.capability_tags || '通用'}</div>
                </div>
                <div class="mt-6 flex items-center justify-between text-xs">
                    <div class="flex items-center gap-x-1.5">
                        <span class="${agent.status === 'ACTIVE_AGENT' ? 'text-emerald-400' : 'text-gray-500'}">●</span>
                        <span class="text-white/70">${agent.status === 'ACTIVE_AGENT' ? '活躍中' : '待命'}</span>
                    </div>
                    <div class="font-mono text-white/40">${agent.base_share_ratio}%</div>
                </div>
            `;
            container.appendChild(card);
        });

        // 重新加入「新增代理」卡片
        container.appendChild(addCard);

    } catch (error) {
        console.warn('無法載入 Agent 列表，保留靜態內容', error);
    }
}
// 新增一個函數，向後端 API 取得真實數據
async function fetchRealtimeStats() {
    try {
        // 1. 取得 Agent 總數 (從 /api/v1/agents 的 total)
        const agentsRes = await fetch('/api/v1/agents?limit=1');
        const agentsData = await agentsRes.json();
        document.getElementById('stat-agents').innerText = agentsData.total || 0;

        // 2. 取得總收益事件數 (從 /api/v1/ledger/realtime 的 items 數量)
        const ledgerRes = await fetch('/api/v1/ledger/realtime');
        const ledgerData = await ledgerRes.json();
        document.getElementById('stat-evo').innerText = ledgerData.items?.length || 0;

        // 3. 系統健康度 (可從 KPI Dashboard 的 avg_kpi 換算，或新增一個 health 端點)
        const kpiRes = await fetch('/api/v1/kpi/dashboard');
        const kpiData = await kpiRes.json();
        const healthScore = Math.round((kpiData.avg_kpi || 1.0) * 99);
        document.getElementById('stat-health').innerText = healthScore;

        // 4. 安全分數 (可保留為固定值，或從守護結界師 Agent 的狀態取得)
        // 此處先保留為 100
        document.getElementById('stat-sec').innerText = '100';
    } catch (error) {
        console.warn('無法取得即時數據，使用靜態備案', error);
    }
}

// 在 initializeApp 中呼叫，並設定每 30 秒自動更新
function initializeApp() {
    // ... 原有初始化 ...
    fetchRealtimeStats();
    setInterval(fetchRealtimeStats, 30000); // 每 30 秒刷新
}
元件 目前狀態 對應你的系統
品牌與敘事 ✅ 7彩主題、帝國榮耀、四大皇/八大將/六聖姬 完美對應你 Lightning-Empire 的世界觀
核心數據佔位 ✅ stat-agents、stat-evo、stat-health、stat-sec 這些就是Ledger + KPI 引擎的輸出點
Agent 卡片 ✅ 14 個預設代理（含名稱、版本、狀態） 可直接與你的 Agent Registry (CSV/DB) 綁定
一鍵動作 ✅ 啟動工廠、部署更新、安全掃描等 6 個按鈕 這些應對應到 Control Tower API (/news/run-pipeline, /agents/start-all 等)
色彩切換 ✅ 7色動態切換功能 可保留作為 UI 樂趣，不影響核心邏輯
順序 新增功能 對應 Agent 說明
1 財經分析 FinanceBot 抓取股市/綠能 ETF 數據，納入播報
2 天氣播報 WeatherBot 串接 Open-Meteo API，播報風場天氣
3 影片生成 VideoBot 將音檔配上靜態畫面或動畫，產出影片
4 自動發布 PublishBot 上傳至 YouTube 或 Podcast 平台
5 Agent 註冊與 Ledger 整合 Control Tower 將這 4 個 Agent 正式納入你的 AI Factory 體系