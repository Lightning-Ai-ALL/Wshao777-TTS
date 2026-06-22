function runAction(actionId) {
    const actionMap = {
        1: { url: '/api/v1/agents/start-all', msg: '⚡ 所有代理已啟動' },
        2: { url: '/api/v1/deploy/update', msg: '🚀 更新已推送' },
        3: { url: '/api/v1/security/scan', msg: '🛡️ 安全掃描完成' },
        4: { url: '/api/v1/sync/devices', msg: '🔄 跨裝置同步完成' },
        5: { url: '/api/v1/backup/core', msg: '💾 核心備份完成' },
        6: { url: '/api/v1/creative/inject', msg: '✨ 創意注入成功' }
    };

    const action = actionMap[actionId];
    if (!action) return;

    // 顯示載入狀態
    showToast(`⏳ 執行中：${action.msg}...`, '#FF9100');

    // 呼叫 API (此處為示範，實際需處理回應)
    fetch(action.url, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            showToast(`✅ ${action.msg} (${data.status || '成功'})`, '#00E676');
        })
        .catch(err => {
            showToast(`❌ 執行失敗：${err.message}`, '#FF1744');
        });
}