import os
import yaml
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pathlib import Path

app = FastAPI(title="Bot Control Tower MVP")

# 載入 Bot 設定
BOT_CONFIG_PATH = Path(__file__).parent / "bots.yaml"
with open(BOT_CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
BOTS = config["bots"]

# 模板（使用簡單內嵌 HTML，或可外掛 templates）
templates = Jinja2Templates(directory=Path(__file__).parent)

def check_bot(token: str) -> bool:
    """檢查 Bot token 是否有效"""
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        r = requests.get(url, timeout=10)
        return r.json().get("ok", False)
    except Exception:
        return False

@app.get("/bots/status")
async def bots_status():
    """回傳所有 Bot 狀態"""
    result = []
    for bot in BOTS:
        token = os.getenv(bot["token_env"])
        alive = False
        if token:
            alive = check_bot(token)
        result.append({
            "id": bot["id"],
            "handle": bot["handle"],
            "role": bot["role"],
            "token_configured": bool(token),
            "alive": alive,
            "token_env": bot["token_env"]
        })
    return {"bots": result}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """顯示 Dashboard 網頁"""
    # 獲取狀態
    status_resp = await bots_status()
    bots = status_resp["bots"]
    # 簡單手寫 HTML
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>⚡ 帝國 Bot 控制塔 ⚡</title>
    <style>
        body { font-family: Arial; background: #0a0f1e; color: #eee; padding: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #2a3; padding: 8px; text-align: left; }
        th { background: #1a2f3a; }
        .alive { color: #0f0; }
        .dead { color: #f00; }
        .btn { background: #2a6; border: none; color: white; padding: 5px 10px; cursor: pointer; }
    </style>
    </head>
    <body>
    <h1>⚡ 帝國 Telegram Bot 軍團狀態 ⚡</h1>
    <table>
        <tr><th>ID</th><th>Handle</th><th>Role</th><th>Token</th><th>狀態</th><th>操作</th></tr>
        {% for bot in bots %}
        <tr>
            <td>{{ bot.id }}</td>
            <td>{{ bot.handle }}</td>
            <td>{{ bot.role }}</td>
            <td>{{ "✅" if bot.token_configured else "❌" }}</td>
            <td class="{{ 'alive' if bot.alive else 'dead' }}">{{ "🟢 存活" if bot.alive else "🔴 死亡" }}</td>
            <td><button class="btn" onclick="restartBot('{{ bot.id }}')">重啟</button></td>
        </tr>
        {% endfor %}
    </table>
    <script>
        async function restartBot(botId) {
            const res = await fetch('/bots/restart', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({bot_id: botId})
            });
            const data = await res.json();
            alert(data.message);
            location.reload();
        }
    </script>
    </body>
    </html>
    """
    from fastapi.templating import TemplateResponse
    # 使用 Jinja2 渲染
    return templates.TemplateResponse("dashboard.html", {"request": request, "bots": bots})

# 為了讓上面 template 能找到，實際應建立 templates/dashboard.html，但為了簡單，使用 HTMLResponse 手動渲染不易。
# 改為直接返回 TemplateResponse，並建立 templates 資料夾。
# 我們簡單處理：直接在代碼中寫死模板路徑
# 但為了完整，下面補上 templates 方式。

# 建立 templates 目錄
TEMPLATE_DIR = Path(__file__).parent / "templates"
TEMPLATE_DIR.mkdir(exist_ok=True)
dashboard_html_path = TEMPLATE_DIR / "dashboard.html"
with open(dashboard_html_path, "w", encoding="utf-8") as f:
    f.write("""<!DOCTYPE html>
<html>
<head><title>⚡ 帝國 Bot 控制塔 ⚡</title>
<style>
    body { font-family: Arial; background: #0a0f1e; color: #eee; padding: 20px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #2a3; padding: 8px; text-align: left; }
    th { background: #1a2f3a; }
    .alive { color: #0f0; }
    .dead { color: #f00; }
    .btn { background: #2a6; border: none; color: white; padding: 5px 10px; cursor: pointer; }
</style>
</head>
<body>
<h1>⚡ 帝國 Telegram Bot 軍團狀態 ⚡</h1>
<table>
    <tr><th>ID</th><th>Handle</th><th>Role</th><th>Token</th><th>狀態</th><th>操作</th></tr>
    {% for bot in bots %}
    <tr>
        <td>{{ bot.id }}</td>
        <td>{{ bot.handle }}</td>
        <td>{{ bot.role }}</td>
        <td>{{ "✅" if bot.token_configured else "❌" }}</td>
        <td class="{{ 'alive' if bot.alive else 'dead' }}">{{ "🟢 存活" if bot.alive else "🔴 死亡" }}</td>
        <td><button class="btn" onclick="restartBot('{{ bot.id }}')">重啟</button></td>
    </tr>
    {% endfor %}
</table>
<script>
async function restartBot(botId) {
    const res = await fetch('/bots/restart', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({bot_id: botId})
    });
    const data = await res.json();
    alert(data.message);
    location.reload();
}
</script>
</body>
</html>""")

templates = Jinja2Templates(directory=TEMPLATE_DIR)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    status_resp = await bots_status()
    bots = status_resp["bots"]
    return templates.TemplateResponse("dashboard.html", {"request": request, "bots": bots})

@app.post("/bots/restart")
async def restart_bot(bot_id: str):
    """簡單模擬重啟：實際應呼叫外部進程管理（如 systemd、docker restart）"""
    # 這裡可以實現真正的重啟邏輯，例如執行 docker restart bot-xxx
    # 目前回傳模擬訊息
    return {"message": f"重啟指令已發送給 {bot_id}（實際需搭配外部進程管理器）"}
  import requests
from app.config import config
from datetime import datetime
import uuid

async def generate_meet_image(scene: str, style: str, girl_image_id: str, auto_save: bool):
    prompt = f"女孩來到{scene}，與 Chih Li Hus 會面，風格：{style}"
    # 這裡替換為實際 API 呼叫
    image_url = "https://placehold.co/600x400?text=Fengjia+Meet+Demo"
    saved_path = None
    if auto_save:
        # 可下載儲存，此處略
        pass
    return {
        "status": "success",
        "prompt": prompt,
        "image_url": image_url,
        "saved_path": saved_path
    }import csv
import json
import yaml
from io import StringIO
from ics import Calendar, Event
from datetime import datetime, timedelta

def export_json(schedule):
    return json.dumps({"schedule": schedule}, ensure_ascii=False, indent=2), "application/json"

def export_yaml(schedule):
    return yaml.dump({"schedule": schedule}, allow_unicode=True), "application/x-yaml"

def export_csv(schedule):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["day", "time", "title", "scene", "style"])
    for idx, day in enumerate(schedule, 1):
        for slot in day["slots"]:
            writer.writerow([idx, slot["time"], slot["title"], slot["scene"], slot["style"]])
    return output.getvalue(), "text/csv"

def export_txt(schedule):
    lines = []
    for idx, day in enumerate(schedule, 1):
        lines.append(f"===== 第{idx}天 ({day['date']}) =====")
        for slot in day["slots"]:
            lines.append(f"{slot['time']} - {slot['title']}")
            lines.append(f"  場景：{slot['scene']}\n  風格：{slot['style']}\n")
    return "\n".join(lines), "text/plain"

def export_js(schedule):
    js = f"export const weekSchedule = {json.dumps(schedule, ensure_ascii=False, indent=2)};"
    return js, "application/javascript"

def export_sh(schedule):
    lines = ["#!/bin/bash", "declare -A SCHEDULE"]
    for idx, day in enumerate(schedule, 1):
        for s_idx, slot in enumerate(day["slots"]):
            key = f"day{idx}_slot{s_idx}"
            value = f"{slot['time']}|{slot['title']}|{slot['scene']}|{slot['style']}"
            lines.append(f"SCHEDULE['{key}']='{value}'")
    lines.append("declare -a DAY_SLOTS")
    for idx, day in enumerate(schedule, 1):
        lines.append(f"DAY_SLOTS[{idx}]={len(day['slots'])}")
    return "\n".join(lines), "text/plain"

def export_gh(schedule):
    lines = ["| Day | Time | Title | Scene | Style |", "| --- | --- | --- | --- | --- |"]
    for idx, day in enumerate(schedule, 1):
        for slot in day["slots"]:
            lines.append(f"| {idx} | {slot['time']} | {slot['title']} | {slot['scene']} | {slot['style']} |")
    return "\n".join(lines), "text/markdown"

def export_factory(schedule):
    data = {"agent": "fengjia_meet", "version": "3.1", "schedule": schedule}
    return json.dumps(data, ensure_ascii=False, indent=2), "application/json"

def export_ics(schedule, base_date=datetime(2026, 6, 20)):
    cal = Calendar()
    for idx, day in enumerate(schedule, 1):
        day_date = base_date + timedelta(days=idx-1)
        for slot in day["slots"]:
            hour, minute = map(int, slot["time"].split(":"))
            start = day_date.replace(hour=hour, minute=minute)
            end = start + timedelta(hours=1)
            event = Event()
            event.name = f"{slot['title']} (逢甲約會)"
            event.begin = start
            event.end = end
            event.description = f"場景：{slot['scene']}\n風格：{slot['style']}"
            cal.events.add(event)
    return str(cal), "text/calendar"

EXPORTERS = {
    "json": export_json,
    "yaml": export_yaml,
    "csv": export_csv,
    "txt": export_txt,
    "js": export_js,
    "sh": export_sh,
    "gh": export_gh,
    "factory": export_factory,
    "ics": export_ics,
}import yaml
from app.config import config

def load_schedule():
    with open(config.SCHEDULE_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("schedule", [])
  import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    GROK_ENDPOINT = os.getenv("GROK_IMAGINE_URL", "https://api.grok.ai/v1/imagine")
    GROK_API_KEY = os.getenv("GROK_API_KEY", "your-api-key")
    OUTPUT_DIR = BASE_DIR / "generated_images"
    EXPORT_DIR = BASE_DIR / "exports"
    SCHEDULE_PATH = BASE_DIR / "app" / "data" / "schedule.yml"

    OUTPUT_DIR.mkdir(exist_ok=True)
    EXPORT_DIR.mkdir(exist_ok=True)

config = Config()
正確的架構（閃電帝國版）

1️⃣ BOT_KEY=sk-07ebe8a0680d48868be230278662fa62
（身份驗證）

```env
BOT_KEY=PRIVATE_KEY_ONLY_YOU=sk-f87f8521f7ec4334b7eb89c898960da5
```

· 這是 Bot 的身份證
· 只能放在 GitHub Secrets
· 名稱建議：LIGHTNING_BOT_KEY=
sk-4597f84add7f4c60a4d3f5636c0db22d
2️⃣ 銀行帳戶（後端資料）

```env
UNION_ACCOUNT_NAME=主權帳戶803
UNION_ACCOUNT_NUMBER=061507123481
```

· 這是 Bot 要用的資料
· 可以：
  · A. 也放 Secrets（安全但手動更新麻煩）
  · B. 放加密的設定檔（Bot 啟動時解密）
  · C. 放後端資料庫（Bot 查詢）

---

🎯 我推薦的「綁法」

✅ 方案 A：全都放 Secrets（簡單、安全）

GitHub Secrets 裡放三筆：

Secret 名稱 值
LIGHTNING_BOT_KEY=sk-4597f84add7f4c60a4d3f5636c0db22d
 PRIVATE_KEY_ONLY_YOU=sk-ddcd683701eb4b9994e6a785c96dc233
UNION_ACCOUNT_NAME 主權帳戶803
UNION_ACCOUNT_NUMBER 061507123481

Workflow 裡：

```yaml
env:
  BOT_KEY: ${{ secrets.LIGHTNING_BOT_KEY }}
  BANK_NAME: ${{ secrets.UNION_ACCOUNT_NAME }}
  BANK_NO: ${{ secrets.UNION_ACCOUNT_NUMBER }}
```

Bot 啟動時：

```js
const bot = new Bot({
  key: process.env.BOT_KEY,
  bank: {
    name: process.env.BANK_NAME,
    number: process.env.BANK_NO
  }
})
```

---

✅ 方案 B：Secrets + 加密設定檔（更靈活）

1. Secrets 只放：
   · LIGHTNING_BOT_KEY=
sk-074c9ee348cb441e9ab8454d4fd50767

   · CONFIG_ENCRYPT_KEY=sk-ddcd683701eb4b9994e6a785c96dc233
2. 銀行資料寫在 .env.bank.encrypted（加密）
3. Bot 啟動時：
   · 用 CONFIG_ENCRYPT_KEY 解密
   · 讀出銀行帳戶

---

✅ 你說的「一起同網頁」

如果你是指：

「能不能在同一個網頁後端，同時處理 Bot 認證 + 銀行匯款？」

答案是 可以，但架構要是：

```
[GitHub Actions] 
    → 啟動 Bot Container
    → Bot 讀取 Secrets (BOT_KEY + 銀行帳戶)
    → Bot 連接銀行 API
    → Bot 提供網頁後端 (Express/Fastify)
```

這樣：

· 同一個 Container
· 同一組環境變數
· 同一個網頁後端
· 同時處理 Bot 指令 + 銀行匯款查詢

---

🚀 你現在要我做的是？

A. 幫你寫一個「Bot + 銀行後端」的 Dockerfile 草案
B. 把這些 Secrets 加到 workflow YAML 裡
C. 兩個都做，順便寫進 MEMORY_CARD.md
