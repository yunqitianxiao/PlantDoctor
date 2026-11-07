/* ============================================================
   history.js — 诊断档案页
   列表渲染 / 筛选 / 分页 / 恢复状态更新 / 删除 / 导出CSV
   ============================================================ */
(function () {
  'use strict';

  const { $, apiFetch, showToast, escapeHtml, formatDate, debounce } = window.PlantDoctor;

  const SEV_NAMES = { healthy: '健康', mild: '轻度', moderate: '中度', severe: '重度' };
  const STATUS_NAMES = { pending: '待跟进', treating: '治疗中', recovered: '已恢复' };
  const ALLOWED_STATUS = ['pending', 'treating', 'recovered'];

  let allRecords = [];
  let trendChart = null;
  const PER_PAGE = 10;
  let currentPage = 1;

  function getFilters() {
    return {
      severity: $('#severityFilter').value,
      status: $('#statusFilter').value,
      query: $('#searchRecord').value.trim().toLowerCase()
    };
  }

  function filteredRecords() {
    const f = getFilters();
    return allRecords.filter((r) => {
      if (f.severity && r.severity_level !== f.severity) return false;
      if (f.status && r.recovery_status !== f.status) return false;
      if (f.query && !(r.disease_name || '').toLowerCase().includes(f.query)) return false;
      return true;
    });
  }

  function renderTable() {
    const list = filteredRecords();
    const start = (currentPage - 1) * PER_PAGE;
    const rows = list.slice(start, start + PER_PAGE);
    const body = $('#historyBody');

    $('#historyEmpty').classList.toggle('hidden', list.length > 0);

    if (!rows.length) {
      body.innerHTML = '<tr><td colspan="6" class="text-center text-muted">暂无记录</td></tr>';
      return;
    }

    body.innerHTML = rows.map((r) => `
      <tr>
        <td><strong>${escapeHtml(r.disease_name)}</strong></td>
        <td><span class="sev-pill sev-${r.severity_level}">${SEV_NAMES[r.severity_level] || r.severity_level}</span></td>
        <td>
          <select class="status-select" data-id="${r.id}" data-status="${r.recovery_status}">
            <option value="pending" ${r.recovery_status === 'pending' ? 'selected' : ''}>待跟进</option>
            <option value="treating" ${r.recovery_status === 'treating' ? 'selected' : ''}>治疗中</option>
            <option value="recovered" ${r.recovery_status === 'recovered' ? 'selected' : ''}>已恢复</option>
          </select>
        </td>
        <td>${((r.confidence || 0) * 100).toFixed(1)}%</td>
        <td>${formatDate(r.created_at)}</td>
        <td>
          <button class="btn btn-ghost btn-sm delete-record" data-id="${r.id}" title="删除">
            <i class="fas fa-trash text-danger"></i>
          </button>
        </td>
      </tr>
    `).join('');

    body.querySelectorAll('.delete-record').forEach((btn) => {
      btn.addEventListener('click', () => deleteRecord(btn.dataset.id));
    });
    body.querySelectorAll('.status-select').forEach((sel) => {
      sel.addEventListener('change', () => updateStatus(sel.dataset.id, sel.value, sel));
    });

    renderPagination(list.length);
    renderStats(list);
    renderTrend(list);
  }

  function renderPagination(total) {
    const pages = Math.ceil(total / PER_PAGE);
    const box = $('#historyPagination');
    if (pages <= 1) { box.innerHTML = ''; return; }
    let html = `<button class="page-btn" data-page="${currentPage - 1}" ${currentPage <= 1 ? 'disabled' : ''}>&laquo;</button>`;
    for (let i = 1; i <= pages; i++) {
      html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }
    html += `<button class="page-btn" data-page="${currentPage + 1}" ${currentPage >= pages ? 'disabled' : ''}>&raquo;</button>`;
    box.innerHTML = html;
    box.querySelectorAll('.page-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const p = Number(btn.dataset.page);
        if (p >= 1 && p <= pages && p !== currentPage) { currentPage = p; renderTable(); }
      });
    });
  }

  /* ---------- 严重程度统计概览 ---------- */
  const severityStats = { healthy: 0, mild: 0, moderate: 0, severe: 0 };

  function renderStats(list) {
    const bySev = { healthy: 0, mild: 0, moderate: 0, severe: 0 };
    let recovered = 0;
    list.forEach((r) => {
      if (bySev[r.severity_level] != null) bySev[r.severity_level] += 1;
      if (r.recovery_status === 'recovered') recovered += 1;
    });
    const set = (id, v) => { const el = $(id); if (el) el.textContent = v; };
    set('#statTotal', list.length);
    set('#statHealthy', bySev.healthy);
    set('#statMild', bySev.mild);
    set('#statModerate', bySev.moderate);
    set('#statSevere', bySev.severe);
    set('#statRecovered', recovered);
  }

  /* ---------- 近 14 天诊断趋势（Chart.js） ---------- */
  function renderTrend(list) {
    const canvas = $('#trendChart');
    if (!canvas || !window.Chart) return;
    const days = [];
    const counts = {};
    const pad = (x) => String(x).padStart(2, '0');
    for (let i = 13; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const key = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
      days.push(key);
      counts[key] = 0;
    }
    list.forEach((r) => {
      const key = String(r.created_at || '').slice(0, 10);
      if (counts[key] != null) counts[key] += 1;
    });
    if (trendChart) { trendChart.destroy(); trendChart = null; }
    trendChart = new window.Chart(canvas.getContext('2d'), {
      type: 'line',
      data: {
        labels: days,
        datasets: [{
          label: '诊断次数',
          data: days.map((k) => counts[k]),
          borderColor: '#2e7d64',
          backgroundColor: 'rgba(46,125,100,.15)',
          fill: true,
          tension: 0.3,
          pointRadius: 3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        plugins: { legend: { display: false } }
      }
    });
  }

  /* ---------- 过期：恢复状态更新 ---------- */
  function updateStatus(id, status, sel) {
    if (!ALLOWED_STATUS.includes(status)) { sel.value = sel.dataset.status; return; }
    apiFetch(`/api/record/${id}/update_status`, {
      method: 'POST',
      body: JSON.stringify({ status })
    })
      .then(() => {
        sel.dataset.status = status;
        showToast('处理状态已更新', 'success');
      })
      .catch((err) => { sel.value = sel.dataset.status; showToast(err.message || '更新失败', 'danger'); });
  }

  function deleteRecord(id) {
    if (!confirm('确定删除这条诊断记录吗？此操作不可撤销。')) return;
    apiFetch(`/api/record/${id}/delete`, { method: 'DELETE' })
      .then(() => {
        showToast('已删除', 'success');
        loadRecords();
      })
      .catch((err) => showToast(err.message || '删除失败', 'danger'));
  }

  /* ---------- 导出 CSV ---------- */
  function exportCsv() {
    const rows = filteredRecords();
    if (!rows.length) { showToast('没有可导出的数据', 'warn'); return; }
    const header = ['病害', '严重程度', '处理状态', '置信度', '病灶占比(%)', '诊断时间'];
    const lines = rows.map((r) => [
      r.disease_name,
      SEV_NAMES[r.severity_level] || r.severity_level,
      STATUS_NAMES[r.recovery_status] || r.recovery_status,
      ((r.confidence || 0) * 100).toFixed(1),
      r.severity_ratio != null ? (r.severity_ratio * 100).toFixed(1) : '',
      r.created_at
    ]);
    const csv = '﻿' + [header, ...lines].map((l) => l.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `植物医生诊断档案_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  /* ---------- 加载 ---------- */
  function loadRecords() {
    apiFetch('/api/user/history_records')
      .then((data) => {
        allRecords = data.records || [];
        currentPage = 1;
        renderTable();
      })
      .catch((err) => {
        $('#historyBody').innerHTML = `<tr><td colspan="6" class="text-center text-danger">${escapeHtml(err.message)}</td></tr>`;
      });
  }

  function bindFilters() {
    $('#severityFilter').addEventListener('change', () => { currentPage = 1; renderTable(); });
    $('#statusFilter').addEventListener('change', () => { currentPage = 1; renderTable(); });
    $('#searchRecord').addEventListener('input', debounce(() => { currentPage = 1; renderTable(); }, 300));
    $('#exportCsvBtn').addEventListener('click', exportCsv);
  }

  function init() {
    bindFilters();
    const trendBtn = $('#trendRefreshBtn');
    if (trendBtn) trendBtn.addEventListener('click', () => renderTrend(filteredRecords()));
    loadRecords();

    /* ---------- 命令面板「导出 CSV」跳转锚点 ---------- */
    function handleHash() {
      if (window.location.hash === '#export-csv') {
        exportCsv();
        history.replaceState(null, '', window.location.pathname);
      }
    }
    window.addEventListener('hashchange', handleHash);
    handleHash();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
