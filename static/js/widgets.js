/* ============================================================
   widgets.js — 通用前端组件库
   选项卡 / 手风琴 / 图片对比滑块 / 严重度仪表 / 复制 /
   CSV 导出 / 打印报告 / 提示气泡   —— 由 data-* 驱动，重复可用
   ============================================================ */
(function (global) {
  'use strict';

  const PD = global.PlantDoctor || {};
  const { $, $$, showToast, escapeHtml } = PD;

  /* ---------- 提示气泡（data-tip 悬停） ---------- */
  function initTooltip() {
    $$('[data-tip]').forEach(function (el) {
      el.addEventListener('mouseenter', function () {
        const tip = document.createElement('div');
        tip.className = 'tooltip-box';
        tip.textContent = el.getAttribute('data-tip') || '';
        document.body.appendChild(tip);
        const r = el.getBoundingClientRect();
        tip.style.top = (r.top - tip.offsetHeight - 8) + 'px';
        tip.style.left = (r.left + r.width / 2 - tip.offsetWidth / 2) + 'px';
        tip.classList.add('show');
        el._tip = tip;
      });
      el.addEventListener('mouseleave', function () {
        if (el._tip) { el._tip.remove(); el._tip = null; }
      });
    });
  }

  /* ---------- 选项卡：<div data-tabs> 内 .tab-btn[data-tab=id]，面板 .tab-pane#id ---------- */
  function initTabs() {
    $$('[data-tabs]').forEach(function (nav) {
      const btns = Array.from(nav.querySelectorAll('.tab-btn'));
      const scope = nav.closest('.tabbed') || document;
      btns.forEach(function (btn) {
        btn.addEventListener('click', function () {
          btns.forEach(function (b) { b.classList.toggle('active', b === btn); });
          scope.querySelectorAll('.tab-pane').forEach(function (pane) {
            pane.classList.toggle('active', pane.id === btn.dataset.tab);
          });
        });
      });
    });
  }

  /* ---------- 手风琴：.accordion-item > .accordion-head ---------- */
  function initAccordion() {
    $$('.accordion-head').forEach(function (head) {
      head.addEventListener('click', function () {
        const item = head.closest('.accordion-item');
        const box = head.parentElement;
        const wasOpen = item.classList.contains('open');
        box.querySelectorAll('.accordion-item.open').forEach(function (i) { i.classList.remove('open'); });
        if (!wasOpen) item.classList.add('open');
      });
    });
  }

  /* ---------- 图片对比滑块：.cmp 内 .cmp-img-before/.cmp-img-after/.cmp-range ---------- */
  function initCompare() {
    $$('.cmp').forEach(function (el) {
      const range = el.querySelector('.cmp-range');
      const after = el.querySelector('.cmp-after');
      const handle = el.querySelector('.cmp-handle');
      if (!range) return;
      function update() {
        const v = Number(range.value) || 0;
        const pw = v + '%';
        if (after) after.style.width = pw;
        if (handle) handle.style.left = pw;
      }
      range.addEventListener('input', update);
      update();
    });
  }

  /* ---------- 严重度仪表：SVG 圆环 stroke-dashoffset ---------- */
  function setGauge(gauge, percent) {
    if (!gauge) return;
    const arc = gauge.querySelector('.gauge-arc');
    if (!arc) return;
    const r = arc.r.baseVal.value;
    const c = 2 * Math.PI * r;
    arc.style.strokeDashoffset = c * (1 - Math.min(Math.max(percent, 0), 100) / 100);
    const num = gauge.querySelector('.gauge-num');
    if (num) num.textContent = Math.round(percent) + '%';
  }

  /* ---------- 复制文本 ---------- */
  function copyText(text, tip) {
    const done = function () { showToast(tip || '已复制到剪贴板', 'success'); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(function () { done(); });
    } else {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); } catch (e) { /* ignore */ }
      ta.remove();
      done();
    }
  }

  /* ---------- CSV 导出 ---------- */
  function downloadCsv(headers, rows, filename) {
    const csv = '﻿' + [headers].concat(rows).map(function (line) {
      return line.map(function (v) {
        return '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
      }).join(',');
    }).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename || ('导出_' + Date.now() + '.csv');
    a.click();
    URL.revokeObjectURL(a.href);
  }

  /* ---------- 打印诊断报告 ---------- */
  const REPORT_CSS =
    'body{font-family:Microsoft YaHei,Arial,sans-serif;color:#1c2b27;margin:24px}' +
    '.rpt{max-width:800px;margin:auto;border:1px solid #dbe4e1;border-radius:10px;padding:20px}' +
    '.rpt h1{color:#2e7d64;font-size:22px;margin:0 0 4px}' +
    '.rpt .sub{color:#5b6b66;font-size:13px;margin-bottom:16px}' +
    '.rpt .row{display:flex;gap:16px;margin:12px 0}' +
    '.rpt img{max-width:48%;border-radius:8px}' +
    '.rpt .grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}' +
    '.rpt .kv{background:#f4f7f6;padding:10px 12px;border-radius:8px;font-size:14px}' +
    '.rpt .kv b{color:#2e7d64}' +
    '.rpt .block{margin:16px 0}' +
    '.rpt .block h3{color:#2e7d64;font-size:16px;border-bottom:1px solid #eef2f0;padding-bottom:6px}';

  function printReport(html) {
    const w = global.open('', '_blank', 'width=900,height=900');
    if (!w) { showToast('浏览器拦截了打印窗口，请允许弹窗后重试', 'warn'); return; }
    w.document.write(
      '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">' +
      '<title>诊断报告</title><style>' + REPORT_CSS + '</style></head><body>' + html + '</body></html>'
    );
    w.document.close();
    setTimeout(function () { w.focus(); w.print(); }, 450);
  }

  /* ---------- 构建诊断报告 HTML ---------- */
  function buildReportCard(data) {
    const levelNames = { healthy: '健康', mild: '轻度', moderate: '中度', severe: '重度' };
    const lvl = levelNames[data.severity_level] || data.severity_level;
    const ratio = Number(data.severity_ratio) || 0;
    const conf = ((data.confidence || 0) * 100).toFixed(1);
    return (
      '<div class="rpt">' +
      '<h1>植物医生 · 病害诊断报告</h1>' +
      '<div class="sub">生成时间 ' + new Date().toLocaleString('zh-CN') + ' · 仅供参考</div>' +
      '<div class="row">' +
        '<img src="' + (data.original_image || '') + '" alt="原图">' +
        '<img src="' + (data.raw_mask_image || data.mask_image || '') + '" alt="病灶掩码">' +
      '</div>' +
      '<div class="grid">' +
        '<div class="kv"><b>识别病害：</b>' + escapeHtml(data.disease_name || '—') + '</div>' +
        '<div class="kv"><b>严重程度：</b>' + lvl + '（病灶占比 ' + ratio.toFixed(1) + '%）</div>' +
        '<div class="kv"><b>识别置信度：</b>' + conf + '%</div>' +
        '<div class="kv"><b>处理建议：</b>' + (data.severity_level === 'severe' ? '立即采取紧急措施' : data.severity_level === 'healthy' ? '加强日常管理' : '针对性用药防治') + '</div>' +
      '</div>' +
      '<div class="block"><h3>治疗方案（大模型增强）</h3><p>' + escapeHtml(data.treatment || '请咨询专业农艺师。') + '</p></div>' +
      '<div class="block"><h3>免责声明</h3><p class="sub">诊断结果仅供参考，使用农药请遵循专业人员指导与当地法规。</p></div>' +
      '</div>'
    );
  }

  /* ---------- 组件统一初始化 ---------- */
  function initAll() {
    initTooltip();
    initTabs();
    initAccordion();
    initCompare();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  /* ---------- 挂到全局命名空间 ---------- */
  PD.setGauge = setGauge;
  PD.copyText = copyText;
  PD.downloadCsv = downloadCsv;
  PD.printReport = printReport;
  PD.buildReportCard = buildReportCard;
  PD.widgets = { initTooltip, initTabs, initAccordion, initCompare };
  global.PlantDoctor = PD;
})(window);
