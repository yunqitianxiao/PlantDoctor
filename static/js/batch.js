/* ============================================================
   batch.js — 批量检测页
   多图上传 / 逐张预测(并发控制) / 进度条 / 结果卡片 / 导出CSV
   ============================================================ */
(function () {
  'use strict';

  const { $, apiFetch, showToast, escapeHtml, debounce } = window.PlantDoctor;

  const results = [];
  const SEV_NAMES = { healthy: '健康', mild: '轻度', moderate: '中度', severe: '重度' };
  const MAX_CONCURRENCY = 3;

  let pending = 0;
  let done = 0;

  const batchDrop = $('#batchDrop');
  const batchInput = $('#batchInput');

  function updateProgress() {
    const total = pending + done;
    $('#batchProgressText').textContent = `${done} / ${total}`;
    const pct = total ? Math.round((done / total) * 100) : 0;
    $('#batchProgressBar').style.width = pct + '%';
  }

  /* ---------- 渲染单张结果 ---------- */
  function renderResult(item) {
    const box = $('#batchResults');
    const div = document.createElement('div');
    div.className = 'batch-item fade-in';
    if (item.error) {
      div.innerHTML = `
        <img src="${item.thumb}" alt="预览">
        <div class="batch-name">${escapeHtml(item.name)}</div>
        <div class="batch-status text-danger">失败：${escapeHtml(item.error)}</div>
      `;
    } else {
      div.innerHTML = `
        <img src="${item.thumb}" alt="预览">
        <div class="batch-name">${escapeHtml(item.disease_name)}</div>
        <div class="batch-status">
          <span class="sev-pill sev-${item.severity_level}">${SEV_NAMES[item.severity_level] || item.severity_level}</span>
          ${((item.confidence || 0) * 100).toFixed(1)}%
        </div>
      `;
    }
    box.appendChild(div);
  }

  /* ---------- 单张预测 ---------- */
  async function predictItem(file) {
    const thumb = await readThumb(file);
    const item = { name: file.name, thumb };
    try {
      const fd = new FormData();
      fd.append('image', file);
      if (fd.get('image')) {
        const data = await apiFetch('/api/predict', { method: 'POST', body: fd });
        item.disease_name = data.disease_name;
        item.confidence = data.confidence;
        item.severity_level = data.severity_level;
        item.severity_ratio = data.severity_ratio;
      }
    } catch (err) {
      item.error = err.message;
    }
    results.push(item);
    done += 1;
    updateProgress();
    renderResult(item);
  }

  function readThumb(file) {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = () => resolve('');
      reader.readAsDataURL(file);
    });
  }

  /* ---------- 并发控制批量检测 ---------- */
  async function runBatch(files) {
    if (!files.length) return;

    $('#batchProgress').classList.remove('hidden');
    $('#batchResults').innerHTML = '';
    pending = files.length;
    done = 0;
    updateProgress();

    const queue = [...files];
    const workers = Array.from({ length: Math.min(MAX_CONCURRENCY, files.length) }, async () => {
      while (queue.length) {
        const file = queue.shift();
        await predictItem(file);
      }
    });
    await Promise.all(workers);
    showToast('批量检测完成', 'success');
  }

  /* ---------- 清空 / 导出 ---------- */
  function clearAll() {
    if (!confirm('确定清空所有检测结果吗？')) return;
    results.length = 0;
    pending = 0;
    done = 0;
    $('#batchResults').innerHTML = '';
    $('#batchProgress').classList.add('hidden');
    batchInput.value = '';
  }

  function exportCsv() {
    if (!results.length) { showToast('没有可导出的结果', 'warn'); return; }
    const header = ['文件名', '病害', '严重程度', '置信度', '病灶占比(%)'];
    const lines = results.map((r) => [
      r.name,
      r.error ? '失败' : r.disease_name,
      r.error ? '' : SEV_NAMES[r.severity_level] || r.severity_level,
      r.error ? '' : ((r.confidence || 0) * 100).toFixed(1),
      r.error ? '' : (r.severity_ratio != null ? Number(r.severity_ratio).toFixed(1) : '')
    ]);
    const csv = '﻿' + [header, ...lines].map((l) => l.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `批量检测结果_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  /* ---------- 初始化 ---------- */
  function init() {
    batchDrop.addEventListener('click', () => batchInput.click());
    batchInput.addEventListener('change', (e) => runBatch(Array.from(e.target.files)));
    batchDrop.addEventListener('dragover', (e) => { e.preventDefault(); batchDrop.classList.add('dragover'); });
    batchDrop.addEventListener('dragleave', () => batchDrop.classList.remove('dragover'));
    batchDrop.addEventListener('drop', (e) => {
      e.preventDefault();
      batchDrop.classList.remove('dragover');
      runBatch(Array.from(e.dataTransfer.files).filter((f) => /image\/(jpeg|png)/.test(f.type)));
    });
    $('#clearBatchBtn').addEventListener('click', clearAll);
    $('#exportBatchCsvBtn').addEventListener('click', exportCsv);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
