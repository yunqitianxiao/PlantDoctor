/* ============================================================
   knowledge.js — 知识百科页
   分类筛选 / 搜索防抖 / 分页 / 病害详情弹窗 / 病历侧栏刷新
   ============================================================ */
(function () {
  'use strict';

  const { $, apiFetch, showToast, escapeHtml, debounce } = window.PlantDoctor;

  const PER_PAGE = 9;
  let currentPage = 1;
  let currentCategory = '';
  let currentQuery = '';
  let totalCount = 0;

  /* ---------- 渲染病害卡片 ---------- */
  function renderDiseases(diseases) {
    const container = $('#diseaseList');
    if (!diseases.length) {
      container.innerHTML = '<div class="empty-state"><i class="fas fa-search"></i><p>未找到相关病害</p></div>';
      return;
    }
    container.innerHTML = diseases.map((d) => `
      <div class="disease-card">
        <div>
          <span class="badge badge-brand category-badge">${escapeHtml(d.category)}</span>
          <h4>${escapeHtml(d.name)}</h4>
          <p>${escapeHtml(d.symptoms)}</p>
        </div>
        <button class="btn btn-soft btn-sm view-detail" data-code="${d.code}">
          <i class="fas fa-book-medical"></i> 查看详情
        </button>
      </div>
    `).join('');

    container.querySelectorAll('.view-detail').forEach((btn) => {
      btn.addEventListener('click', () => loadDetail(btn.dataset.code));
    });
  }

  /* ---------- 分页 ---------- */
  function renderPagination() {
    const pages = Math.ceil(totalCount / PER_PAGE);
    const box = $('#pagination');
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
        if (p >= 1 && p <= pages && p !== currentPage) loadDiseases(p);
      });
    });
  }

  /* ---------- 加载病害列表 ---------- */
  function loadDiseases(page) {
    currentPage = page || 1;
    $('#resultCount').textContent = '加载中...';
    const q = currentQuery ? `&q=${encodeURIComponent(currentQuery)}` : '';
    apiFetch(`/api/diseases?page=${currentPage}&per_page=${PER_PAGE}&category=${encodeURIComponent(currentCategory)}${q}`)
      .then((data) => {
        totalCount = data.total || 0;
        $('#resultCount').textContent = `共 ${totalCount} 条`;
        renderDiseases(data.diseases || []);
        renderPagination();
      })
      .catch((err) => showToast(err.message || '加载失败', 'danger'));
  }

  /* ---------- 搜索 ---------- */
  function runSearch() {
    currentQuery = $('#searchInput').value.trim();
    $('#clearSearchBtn').classList.toggle('hidden', !currentQuery);
    loadDiseases(1);
  }

  /* ---------- 病害详情弹窗 ---------- */
  function loadDetail(code) {
    apiFetch(`/api/disease/${code}`)
      .then((d) => {
        $('#modalTitle').textContent = d.name;
        $('#modalSymptoms').textContent = d.symptoms || '—';
        $('#modalCauses').textContent = d.causes || '—';
        $('#modalTreatment').textContent = d.treatment || '—';
        $('#modalPrevention').textContent = d.prevention || '—';
        $('#diseaseModal').style.display = 'flex';
      })
      .catch((err) => showToast(err.message || '详情加载失败', 'danger'));
  }

  /* ---------- 病历侧栏 ---------- */
  function loadHistory() {
    apiFetch('/api/user/history_records')
      .then((data) => {
        const list = $('#historyRecordsList');
        const records = data.records || [];
        if (!records.length) {
          list.innerHTML = '<div class="empty-state"><p>暂无病历</p></div>';
          return;
        }
        list.innerHTML = records.slice(0, 8).map((r) => `
          <div class="history-item">
            <div>
              <div class="history-name">${escapeHtml(r.disease_name)}</div>
              <div class="history-meta">${r.severity_level} · ${(r.created_at || '').slice(0, 10)}</div>
            </div>
            <button class="btn btn-ghost btn-sm delete-record" data-id="${r.id}" title="删除">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        `).join('');
        list.querySelectorAll('.delete-record').forEach((btn) => {
          btn.addEventListener('click', () => deleteRecord(btn.dataset.id));
        });
      })
      .catch(() => {});
  }

  function deleteRecord(id) {
    if (!confirm('确定删除这条诊断记录吗？')) return;
    apiFetch(`/api/record/${id}/delete`, { method: 'DELETE' })
      .then(() => {
        showToast('已删除', 'success');
        loadHistory();
      })
      .catch((err) => showToast(err.message || '删除失败', 'danger'));
  }

  /* ---------- 初始化 ---------- */
  function init() {
    // 分类筛选
    $('#categoryFilter').querySelectorAll('.chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        $('#categoryFilter').querySelectorAll('.chip').forEach((c) => c.classList.remove('active'));
        chip.classList.add('active');
        currentCategory = chip.dataset.category;
        loadDiseases(1);
      });
    });

    // 搜索防抖
    $('#searchInput').addEventListener('input', debounce(runSearch, 350));
    $('#clearSearchBtn').addEventListener('click', () => {
      $('#searchInput').value = '';
      runSearch();
    });

    // 弹窗关闭
    $('#diseaseModal').querySelectorAll('[data-close]').forEach((btn) => {
      btn.addEventListener('click', () => { $('#diseaseModal').style.display = 'none'; });
    });
    $('#diseaseModal').addEventListener('click', (e) => {
      if (e.target === $('#diseaseModal')) $('#diseaseModal').style.display = 'none';
    });
    $('#modalDiagBtn').addEventListener('click', () => { window.location.href = '/diagnose'; });

    $('#refreshHistoryBtn').addEventListener('click', loadHistory);

    loadDiseases(1);
    loadHistory();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
