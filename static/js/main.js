/* ============================================================
   main.js — 全局前端工具库
   主题切换 / 移动端导航 / Toast / 弹窗 / confirm / fetch 封装 / 工具函数
   ============================================================ */
(function (global) {
  'use strict';

  /* ---------- 常用查询简写 ---------- */
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  /* ---------- 工具函数 ---------- */
  function debounce(fn, wait) {
    let timer = null;
    return function debounced(...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), wait);
    };
  }

  function throttle(fn, wait) {
    let last = 0;
    return function throttled(...args) {
      const now = Date.now();
      if (now - last >= wait) {
        last = now;
        fn.apply(this, args);
      }
    };
  }

  function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatNumber(n) {
    if (n == null || isNaN(n)) return '0';
    return Number(n).toLocaleString('zh-CN');
  }

  function formatDate(dt) {
    if (!dt) return '—';
    const d = new Date(dt);
    if (isNaN(d.getTime())) return String(dt);
    const pad = (x) => String(x).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  /* ---------- 主题切换 ---------- */
  const THEME_KEY = 'plant-doctor-theme';

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
    const icon = $('#themeToggle i');
    if (icon) icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
  }

  function initTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    const prefersDark = global.matchMedia && global.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(saved || (prefersDark ? 'dark' : 'light'));
  }

  /* ---------- Toast 通知 ---------- */
  const TOAST_ICONS = { success: 'fa-check-circle', danger: 'fa-exclamation-circle', warn: 'fa-exclamation-triangle', info: 'fa-info-circle' };

  function showToast(message, type = 'info', duration = 3000) {
    const container = $('#toastContainer');
    if (!container) {
      alert(message);
      return;
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = TOAST_ICONS[type] || TOAST_ICONS.info;
    toast.innerHTML = `
      <i class="fas ${icon}"></i>
      <span class="text-small">${escapeHtml(message)}</span>
      <button class="toast-close" aria-label="关闭">&times;</button>
    `;
    container.appendChild(toast);
    const dismiss = () => {
      toast.classList.add('out');
      setTimeout(() => toast.remove(), 260);
    };
    toast.querySelector('.toast-close').addEventListener('click', dismiss);
    if (duration > 0) setTimeout(dismiss, duration);
  }

  /* ---------- 弹窗 ---------- */
  function openModal(id) {
    const el = $(`#${id}`);
    if (el) {
      el.classList.remove('hidden');
      el.style.display = 'flex';
    }
  }

  function closeModal(id) {
    const el = $(`#${id}`);
    if (el) {
      el.style.display = 'none';
    }
  }

  function closeAllModals() {
    $$('.modal-backdrop').forEach((m) => { m.style.display = 'none'; });
  }

  /* ---------- fetch 封装 ---------- */
  async function apiFetch(url, options = {}) {
    const opts = Object.assign({ headers: {} }, options);
    if (opts.body && !(opts.body instanceof FormData)) {
      opts.headers['Content-Type'] = 'application/json';
    }
    const res = await fetch(url, opts);
    if (res.status === 401) {
      showToast('登录已过期，请重新登录', 'warn');
      setTimeout(() => { global.location.href = '/login'; }, 800);
      throw new Error('Unauthorized');
    }
    let data = null;
    try { data = await res.json(); } catch (e) { /* 非 JSON 响应 */ }
    if (!res.ok) {
      const msg = (data && (data.error || data.message)) || `请求失败 (${res.status})`;
      throw new Error(msg);
    }
    return data;
  }

  /* ---------- 确认对话框 ---------- */
  function confirmDialog(message, onConfirm, opts = {}) {
    const title = opts.title || '请确认';
    const confirmText = opts.confirmText || '确定';
    const danger = opts.danger !== false;
    // 简易确认
    if (global.confirm(message)) {
      onConfirm();
    }
  }

  /* ---------- 下拉刷新 / 数字动画 ---------- */
  function animateNumber(el, target, duration = 900) {
    const start = 0;
    const startTime = performance.now();
    function tick(now) {
      const p = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      const val = Math.round(start + (target - start) * eased);
      el.textContent = formatNumber(val);
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  /* ---------- 全局初始化 ---------- */
  function initGlobal() {
    initTheme();

    // 主题切换按钮
    const themeBtn = $('#themeToggle');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        applyTheme(current === 'dark' ? 'light' : 'dark');
      });
    }

    // 移动端导航
    const navToggle = $('#navToggle');
    const navLinks = $('#navLinks');
    if (navToggle && navLinks) {
      navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
    }

    // 点击弹窗背景关闭
    $$('.modal-backdrop').forEach((backdrop) => {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) closeAllModals();
      });
    });
  }

  /* ---------- 导出全局命名空间 ---------- */
  const PlantDoctor = {
    $, $$, debounce, throttle, escapeHtml,
    formatNumber, formatDate, showToast,
    openModal, closeModal, closeAllModals,
    apiFetch, confirmDialog, animateNumber,
    applyTheme, initTheme
  };

  global.PlantDoctor = PlantDoctor;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGlobal);
  } else {
    initGlobal();
  }
})(window);
