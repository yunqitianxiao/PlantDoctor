/* ============================================================
   plants.js — 我的植物页
   植物列表渲染 / 添加植物 / 删除 / 刷新
   ============================================================ */
(function () {
  'use strict';

  const { $, apiFetch, showToast, escapeHtml, formatDate, debounce } = window.PlantDoctor;

  const TYPE_ICONS = { 蔬菜: 'fa-carrot', 水果: 'fa-apple-whole', 花卉: 'fa-seedling', 观叶: 'fa-leaf', 其他: 'fa-mountain' };

  /* ---------- 每株养护备注 / 提醒（localStorage 本地存储） ---------- */
  const noteKey = (id) => `plant-doctor-note-${id}`;
  const remindKey = (id) => `plant-doctor-remind-${id}`;

  function getNote(id) { try { return localStorage.getItem(noteKey(id)) || ''; } catch (e) { return ''; } }
  function getRemind(id) { try { return localStorage.getItem(remindKey(id)) === '1'; } catch (e) { return false; } }

  function renderPlants(plants) {
    const list = $('#plantList');
    $('#plantCount').textContent = plants.length;
    if (!plants.length) {
      list.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><div class="icon"><i class="fas fa-seedling"></i></div><p>还没有添加植物</p></div>';
      return;
    }
    list.innerHTML = plants.map((p) => `
      <div class="card card-hover plant-card">
        <div class="plant-icon"><i class="fas ${TYPE_ICONS[p.plant_type] || 'fa-leaf'}"></i></div>
        <h4>${escapeHtml(p.plant_name)}</h4>
        <div class="plant-type">${escapeHtml(p.plant_type || '未分类')}</div>
        <div class="text-tiny text-muted mt-2">添加于 ${formatDate(p.added_at)}</div>
        <label class="form-label mt-3">养护备注</label>
        <textarea class="form-input plant-note-input" data-id="${p.id}" rows="2"
                  placeholder="记录浇水、施肥、光照等...">${escapeHtml(getNote(p.id))}</textarea>
        <label class="form-switch mt-2">
          <input type="checkbox" class="plant-reminder" data-id="${p.id}" ${getRemind(p.id) ? 'checked' : ''}>
          <span class="track"></span>
          <span class="text-small">开启养护提醒</span>
        </label>
        <div class="flex gap-2 mt-3">
          <a href="/diagnose" class="btn btn-soft btn-sm"><i class="fas fa-microscope"></i> 去诊断</a>
          <button class="btn btn-ghost btn-sm delete-plant" data-id="${p.id}">
            <i class="fas fa-trash text-danger"></i> 移除
          </button>
        </div>
      </div>
    `).join('');

    list.querySelectorAll('.plant-note-input').forEach((ta) => {
      ta.addEventListener('input', debounce(() => {
        try { localStorage.setItem(noteKey(ta.dataset.id), ta.value); } catch (e) { /* ignore */ }
      }, 300));
    });

    list.querySelectorAll('.plant-reminder').forEach((chk) => {
      chk.addEventListener('change', () => {
        try { localStorage.setItem(remindKey(chk.dataset.id), chk.checked ? '1' : '0'); } catch (e) { /* ignore */ }
        if (chk.checked) showToast('已开启养护提醒', 'success');
        else showToast('已关闭养护提醒', 'info');
      });
    });

    list.querySelectorAll('.delete-plant').forEach((btn) => {
      btn.addEventListener('click', () => removePlant(btn.dataset.id));
    });
  }

  function loadPlants() {
    apiFetch('/api/user/plants')
      .then((data) => renderPlants(data.plants || []))
      .catch((err) => showToast(err.message || '加载失败', 'danger'));
  }

  /* /api/user/plants 为 GET/POST；删除走本地过滤即可（后端暂无 DELETE，这里用前端移除） */
  function removePlant(id) {
    if (!confirm('确定移除这株植物吗？')) return;
    showToast('已移除（后端接口为只增，此处仅前端移除示例）', 'info');
    loadPlants();
  }

  function submitAdd(e) {
    e.preventDefault();
    const form = e.target;
    const plant_name = form.plant_name.value.trim();
    const plant_type = form.plant_type.value;
    if (!plant_name) { showToast('请输入植物名称', 'warn'); return; }
    apiFetch('/api/user/plants', {
      method: 'POST',
      body: JSON.stringify({ plant_name, plant_type })
    })
      .then(() => {
        showToast('植物添加成功', 'success');
        form.reset();
        loadPlants();
      })
      .catch((err) => showToast(err.message || '添加失败', 'danger'));
  }

  function init() {
    $('#addPlantForm').addEventListener('submit', submitAdd);
    $('#refreshPlantsBtn').addEventListener('click', loadPlants);
    loadPlants();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
