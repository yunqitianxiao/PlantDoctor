/* ============================================================
   dashboard.js — 仪表盘数据与图表
   统计卡数字动画 / 严重程度环形图 / 植物类别柱状图
   ============================================================ */
(function () {
  'use strict';

  const { $, animateNumber, formatNumber, showToast } = window.PlantDoctor;

  // 服务端渲染到页面的植物统计
  const plantStats = (window.PLANT_STATS || {});
  const hasChartjs = typeof window.Chart !== 'undefined';

  const SEV_LABELS = { healthy: '健康', mild: '轻度', moderate: '中度', severe: '重度' };
  const SEV_COLORS = { healthy: '#2e7d64', mild: '#f4a261', moderate: '#e76f51', severe: '#e63946' };

  /* ---------- 统计卡数字动画 ---------- */
  async function loadStats() {
    try {
      const data = await window.PlantDoctor.apiFetch('/api/dashboard/stats');
      const els = [
        ['totalDiagnoses', data.total_diagnoses || 0],
        ['healthyCount', data.healthy_count || 0],
        ['diseaseCount', data.disease_count || 0]
      ];
      els.forEach(([id, val]) => {
        const el = document.getElementById(id);
        if (el) animateNumber(el, val);
      });
      renderSeverityChart(data.severity_distribution || {});
    } catch (err) {
      showToast(err.message || '统计加载失败', 'danger');
    }
  }

  /* ---------- 严重程度环形图 ---------- */
  function renderSeverityChart(distribution) {
    if (!hasChartjs || !$('#severityChart')) return;
    const labels = ['mild', 'moderate', 'severe'].filter((k) => distribution[k] > 0);
    if (labels.length === 0) {
      // 全是健康或无记录
      renderSeverityEmpty();
      return;
    }
    const data = labels.map((k) => distribution[k]);
    new Chart($('#severityChart'), {
      type: 'doughnut',
      data: {
        labels: labels.map((k) => SEV_LABELS[k] || k),
        datasets: [{
          data,
          backgroundColor: labels.map((k) => SEV_COLORS[k]),
          borderColor: '#ffffff',
          borderWidth: 3,
          hoverOffset: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { usePointStyle: true, padding: 18 } },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.parsed} 次`
            }
          }
        }
      }
    });
  }

  function renderSeverityEmpty() {
    const box = $('#severityChart');
    if (!box) return;
    box.parentNode.classList.remove('chart-box');
    box.insertAdjacentHTML('beforebegin',
      '<div class="empty-state"><i class="fas fa-check-circle"></i><p>暂无病害记录，一切健康</p></div>');
    box.remove();
  }

  /* ---------- 植物类别柱状图 ---------- */
  function renderPlantChart() {
    if (!hasChartjs || !$('#plantChart')) return;
    const entries = Object.entries(plantStats);
    if (entries.length === 0) return;
    const labels = entries.map(([k]) => k);
    const values = entries.map(([, v]) => v);
    new Chart($('#plantChart'), {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: '诊断次数',
          data: values,
          backgroundColor: 'rgba(46,125,100,0.75)',
          borderRadius: 8,
          maxBarThickness: 46
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (ctx) => ` ${ctx.parsed.y} 次` } }
        },
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1 }, grid: { color: 'rgba(0,0,0,0.06)' } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  function init() {
    loadStats();
    renderPlantChart();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
