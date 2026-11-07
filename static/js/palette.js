/* ============================================================
   palette.js — 命令面板（Command Palette）
   Ctrl / Cmd + K 呼出，输入页面名或操作快速跳转；
   支持模糊匹配、上下方向键选择、回车执行、ESC 关闭。
   依赖 main.js 暴露的 window.PlantDoctor 工具函数。
   ============================================================ */
(function (global) {
  'use strict';

  const { $, $$, showToast, applyTheme } = global.PlantDoctor;

  /* ---------- 菜单项定义：页面 + 操作 ---------- */
  // section 用于分组；href 表示跳转页面；run 表示就地执行的动作
  function buildEntries() {
    const loggedIn = Boolean(localStorage.getItem('plant-doctor-auth')) ||
      Boolean((document.querySelector('.nav-user') || {}).textContent &&
        global.location.pathname !== '/login');
    const entries = [
      { section: '页面', icon: 'fa-tachometer-alt', label: '仪表盘', keywords: '首页 概览 统计 dashboard home', href: '/' },
      { section: '页面', icon: 'fa-microscope', label: '智能诊断', keywords: '识别 上传 图片 检测 diagnose identify', href: '/diagnose' },
      { section: '页面', icon: 'fa-images', label: '批量检测', keywords: '多图 并发 批量 detect', href: '/detect-batch' },
      { section: '页面', icon: 'fa-book-open', label: '植物百科', keywords: '知识库 病害 症状 治疗 预防 knowledge', href: '/knowledge' },
      { section: '页面', icon: 'fa-notes-medical', label: '诊断档案', keywords: '历史 记录 病历 状态 history', href: '/history' },
      { section: '页面', icon: 'fa-seedling', label: '我的植物', keywords: '养护 植物 档案 plants', href: '/plants' },
      { section: '页面', icon: 'fa-info-circle', label: '关于系统', keywords: '架构 模型 免责 about', href: '/about' },
      { section: '页面', icon: 'fa-right-to-bracket', label: '登录 / 注册', keywords: '登陆 账号 login', href: '/login' }
    ];

    const actions = [
      { section: '操作', icon: 'fa-moon', label: '切换明暗主题', keywords: 'dark light 深色 浅色 主题', run: function () {
        const cur = global.document.documentElement.getAttribute('data-theme');
        applyTheme(cur === 'dark' ? 'light' : 'dark');
        showToast(cur === 'dark' ? '已切换为浅色主题' : '已切换为深色主题', 'success');
      } },
      { section: '操作', icon: 'fa-link', label: '复制当前页面链接', keywords: 'copy url 链接', run: function () {
        const text = global.location.href;
        if (global.navigator.clipboard && global.navigator.clipboard.writeText) {
          global.navigator.clipboard.writeText(text).then(function () {
            showToast('已复制当前页面链接', 'success');
          });
        } else {
          window.prompt('复制当前页面链接：', text);
        }
      } },
      { section: '操作', icon: 'fa-print', label: '打印当前诊断报告', keywords: 'print pdf 报告 打印', run: function () {
        const pd = global.PlantDoctor;
        const data = global.__lastResult;
        if (pd && data && pd.buildReportCard && pd.printReport) {
          pd.printReport(pd.buildReportCard(data));
        } else if (global.location.pathname === '/diagnose') {
          showToast('请先完成一次诊断再打印报告', 'warn');
        } else {
          showToast('请前往「智能诊断」页生成报告后打印', 'warn');
        }
      } },
      { section: '操作', icon: 'fa-download', label: '导出诊断记录 CSV', keywords: 'csv 导出 export 档案', run: function () {
        global.location.href = '/history#export-csv';
      } },
      { section: '操作', icon: 'fa-arrow-up', label: '回到页首', keywords: 'top scroll 顶部 复习', run: function () {
        global.scrollTo({ top: 0, behavior: 'smooth' });
      } }
    ];
    return entries.concat(actions);
  }

  /* ---------- 模糊匹配评分 ---------- */
  function scoreQuery(query, text) {
    query = (query || '').toLowerCase();
    text = (text || '').toLowerCase();
    if (!query) return 1;
    if (text === query) return 1000;
    let qi = 0, score = 0, streak = 0;
    for (let i = 0; i < text.length; i++) {
      if (text[i] === query[qi]) {
        qi++;
        streak++;
        score += 2 + streak;
        if (i === 0 || text[i - 1] === ' ' || text[i - 1] === '/') score += 5;
        if (qi === query.length) return score;
      } else {
        streak = 0;
      }
    }
    return qi === query.length ? score : 0;
  }

  /* ---------- 渲染结果列表 ---------- */
  function renderResults(listEl, query) {
    const entries = buildEntries();
    const matches = [];
    entries.forEach(function (e) {
      const hay = e.label + ' ' + (e.keywords || '');
      const s = scoreQuery(query, hay) + scoreQuery(query, e.label);
      if (s > 0) matches.push({ e: e, s: s });
    });
    matches.sort(function (a, b) { return b.s - a.s; });

    const MAX = 40;
    const shown = matches.slice(0, MAX);
    let html = '';
    let lastSection = null;
    shown.forEach(function (m, idx) {
      if (m.e.section !== lastSection) {
        lastSection = m.e.section;
        html += '<div class="palette-group">' + lastSection + '</div>';
      }
      html += '<div class="palette-item" data-idx="' + idx + '" role="option">' +
        '<i class="fas ' + m.e.icon + '"></i>' +
        '<span class="palette-label">' + m.e.label + '</span>' +
        '<span class="palette-arrow">&rarr;</span>' +
        '</div>';
    });

    if (!shown.length) {
      html = '<div class="palette-empty">没有匹配项，试试「诊断」「导出」「百科」</div>';
      listEl.innerHTML = html;
      return { items: [], active: -1 };
    }

    listEl.innerHTML = html;
    const items = Array.from(listEl.querySelectorAll('.palette-item'));
    items.forEach(function (el) {
      el.addEventListener('mousemove', function () {
        selectIndex(items, Number(el.dataset.idx));
      });
      el.addEventListener('click', function () {
        runItem(entries, Number(el.dataset.idx), shown);
      });
    });
    return { items: items, active: 0 };
  }

  /* ---------- 高亮与执行 ---------- */
  function selectIndex(items, idx) {
    items.forEach(function (el) {
      el.classList.toggle('active', Number(el.dataset.idx) === idx);
    });
  }

  function runItem(entries, idx, shown) {
    const m = shown && shown[idx];
    if (!m) return;
    if (m.e.run) {
      m.e.run();
    } else if (m.e.href) {
      global.location.href = m.e.href;
    }
    close();
  }

  /* ---------- 面板开关 ---------- */
  let current = { items: [], active: -1, shown: [] };
  let lastFocused = null;

  function open() {
    const overlay = $('#paletteOverlay');
    const input = $('#paletteInput');
    const list = $('#paletteList');
    if (!overlay) return;
    lastFocused = document.activeElement;
    overlay.hidden = false;
    overlay.classList.add('open');
    input.value = '';
    current = renderResults(list, '');
    input.focus();
  }

  function close() {
    const overlay = $('#paletteOverlay');
    if (!overlay) return;
    overlay.hidden = true;
    overlay.classList.remove('open');
    if (lastFocused && lastFocused.focus) lastFocused.focus();
  }

  function move(delta) {
    const items = current.items;
    if (!items.length) return;
    let next = current.active + delta;
    if (next < 0) next = items.length - 1;
    if (next >= items.length) next = 0;
    selectIndex(items, next);
    current.active = next;
    const el = items[next];
    if (el && el.scrollIntoView) el.scrollIntoView({ block: 'nearest' });
  }

  /* ---------- 全局键盘绑定 ---------- */
  function onGlobalKey(e) {
    // Ctrl / Cmd + K 呼出
    if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
      e.preventDefault();
      const overlay = $('#paletteOverlay');
      if (overlay && !overlay.hidden) { close(); } else { open(); }
      return;
    }
    if (e.key === 'Escape') { close(); }
  }

  function onInputKey(e) {
    if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      runItem(buildEntries(), current.active, current.shown);
    }
  }

  function bindInput() {
    const input = $('#paletteInput');
    const list = $('#paletteList');
    if (!input) return;
    input.addEventListener('keydown', onInputKey);
    input.addEventListener('input', function () {
      current = renderResults(list, input.value);
      var active = current.items[current.active];
      if (active) active.classList.add('active');
    });
  }

  function bindToggleButton() {
    const btn = $('#paletteBtn');
    if (btn) btn.addEventListener('click', open);
  }

  function bindOverlayClose() {
    const overlay = $('#paletteOverlay');
    if (overlay) {
      overlay.addEventListener('click', function (e) {
        if (e.target === overlay) close();
      });
    }
  }

  /* ---------- 初始化 ---------- */
  function init() {
    bindInput();
    bindToggleButton();
    bindOverlayClose();
    global.addEventListener('keydown', onGlobalKey);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})(window);
