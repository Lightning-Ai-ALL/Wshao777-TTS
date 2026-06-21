#!/bin/bash
# ============================================
# Storm Army & Population Ops - Termux 優化版
# ============================================

set -e  # 遇錯即停，避免繼續亂跑

echo "🌀 啟動 Storm Army 操作程序..."

# 1. 檢查目錄
if [ ! -d "storm_army" ]; then
    echo "❌ 找不到 storm_army 目錄，請先建立或修改路徑"
    exit 1
fi
cd storm_army

# 2. 安裝必要套件（安靜模式）
echo "📦 檢查 Python 依賴..."
pip install -q requests bs4 2>/dev/null || echo "⚠️ 部分套件安裝失敗，請手動執行 pip install requests bs4"

# 3. 檢查核心檔案
if [ ! -f "aibot_sim.py" ]; then
    echo "⚠️ 警告：aibot_sim.py 不存在，跳過模擬"
else
    echo "🤖 執行三軍示範..."
    python aibot_sim.py --demo-bot || echo "⚠️ 模擬執行失敗"
fi

# 4. 人口合併（僅當 JSON 存在）
if [ -f "real_world_state.json" ]; then
    echo "👥 執行人口合併（瑞士 → 台灣）..."
    python - <<'PY'
import json, sys
try:
    from population_ops import merge_population, PopEventLog
except ImportError:
    print("❌ 缺少 population_ops 模組，跳過合併")
    sys.exit(0)

with open("real_world_state.json","r+",encoding="utf-8") as f:
    data = json.load(f)

plan = [
    {"zone":"台中-西屯安全區","cap":4000000},
    {"zone":"台北-北投守護區","cap":3000000},
    {"zone":"新竹-竹北科研區","cap":3700000},
    {"zone":"南投-日月潭安全區","cap":4000000}
]

result = merge_population(data, "瑞士", "台灣", amount="all", cluster_plan=plan, log=PopEventLog("events.log"))
print(f"✅ 搬遷 {result['moved']} 人")
for a in result["assigned"]:
    print(f"  - {a['zone']}：{a['assigned']} 人")

with open("real_world_state.json","w",encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
PY
else
    echo "⚠️ real_world_state.json 不存在，跳過人口合併"
fi

# 5. 單元測試（僅當有 test 資料夾）
if [ -d "tests" ] || [ -f "test_*.py" ]; then
    echo "🧪 執行單元測試..."
    python -m unittest -v || echo "⚠️ 測試有失敗"
else
    echo "⏭️ 無測試檔案，跳過"
fi

echo "✅ 所有操作完成！"