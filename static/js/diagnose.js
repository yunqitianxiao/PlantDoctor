/* ============================================================
   diagnose.js — 智能诊断页
   上传 / 拖拽 / 预测 / 病灶叠加(canvas) / 结果渲染 / 步骤条
   ============================================================ */
(function () {
  'use strict';

  const { $, showToast, apiFetch, escapeHtml, setGauge, buildReportCard, printReport } = window.PlantDoctor;

  let currentOriginal = null;   // 原图 dataURL
  let currentMask = null;       // 原始病灶掩码(透明底) dataURL
  let currentRisk = 50;         // 默认透明度(后端已按 0.5 合成)
  let creatingOverlay = false;

  const uploadArea = $('#uploadArea');
  const imageInput = $('#imageInput');
  const overlayCanvas = $('#overlayCanvas');
  const ctx = overlayCanvas ? overlayCanvas.getContext('2d') : null;

  /* ---------- 步骤条控制 ---------- */
  function setStep(step) {
    document.querySelectorAll('[data-step]').forEach((el) => {
      const n = Number(el.dataset.step);
      el.classList.toggle('active', n === step);
      el.classList.toggle('done', n < step);
    });
  }

  /* ---------- 重新绘制叠加层 ---------- */
  function drawOverlay() {
    if (!currentOriginal || !overlayCanvas || !ctx) return;

    const img = new Image();
    img.onload = () => {
      // 以预览框实际大小为准
      const wrap = overlayCanvas.parentElement;
      const boxW = wrap.clientWidth || 384;
      const boxH = wrap.clientHeight || 384;
      overlayCanvas.width = boxW;
      overlayCanvas.height = boxH;
      ctx.clearRect(0, 0, boxW, boxH);

      // 原图按 contain 放入画布
      const scale = Math.min(boxW / img.width, boxH / img.height);
      const dw = img.width * scale;
      const dh = img.height * scale;
      const dx = (boxW - dw) / 2;
      const dy = (boxH - dh) / 2;
      ctx.drawImage(img, dx, dy, dw, dh);

      if (!$('#toggleOverlay').checked || !currentMask) return;

      const maskImg = new Image();
      maskImg.onload = () => {
        const alpha = Number($('#alphaSlider').value) / 100;
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.drawImage(maskImg, dx, dy, dw, dh);
        ctx.restore();
      };
      maskImg.src = currentMask;
    };
    img.src = currentOriginal;
  }

  function updateAlphaLabel() {
    const val = $('#alphaSlider').value;
    $('#alphaValue').textContent = val + '%';
  }

  /* ---------- 渲染诊断结果 ---------- */
  function renderResult(data) {
    $('#diseaseName').textContent = data.disease_name;
    $('#confidence').textContent = `置信度：${(data.confidence * 100).toFixed(1)}%`;

    const ratio = Number(data.severity_ratio) || 0;
    const level = data.severity_level || 'healthy';
    const levelNames = { healthy: '健康', mild: '轻度', moderate: '中度', severe: '重度' };

    $('#scoreValue').textContent = (data.confidence * 100).toFixed(1) + '%';
    $('#severityValue').textContent = ratio.toFixed(1) + '%';
    $('#statusValue').textContent = levelNames[level] || level;

    const tag = $('#severityLevelTag');
    tag.textContent = (levelNames[level] || level) + ' · ' + ratio.toFixed(1) + '%';
    tag.className = `badge badge-${level === 'healthy' ? 'success' : level === 'mild' ? 'warn' : 'danger'}`;

    $('#severityFill').style.width = Math.min(ratio, 100) + '%';
    $('#treatmentText').textContent = data.treatment || '暂无方案，请咨询专业农艺师。';

    // 严重度圆环仪表（可复用于诊断报告与结果卡片）
    const gaugeEl = $('#severityGauge');
    if (gaugeEl) {
      setGauge(gaugeEl, Math.min(ratio, 100));
      $('#gaugeLevel').textContent = levelNames[level] || level;
    }

    // 记录最近一次结果，供导出/打印报告使用
    window.__lastResult = data;

    // 症状标签
    $('#symptomTags').innerHTML = [
      `<span class="sev-pill sev-${level}">${levelNames[level] || level}</span>`,
      `<span class="badge badge-brand">${escapeHtml(data.disease_name)}</span>`,
      `<span class="badge badge-neutral">病灶 ${ratio.toFixed(1)}%</span>`
    ].join('');

    currentOriginal = data.original_image;
    currentMask = data.raw_mask_image || null;   // 透明底掩码，用于可调叠加
    $('#maskPreview').src = data.mask_image || '';
    $('#maskPreview').style.display = data.mask_image ? 'block' : 'none';
    $('#overlayCanvas').style.display = currentMask ? 'block' : 'none';

    $('#previewContainer').classList.remove('hidden');
    $('#resultArea').classList.remove('hidden');
    setStep(3);
    requestAnimationFrame(drawOverlay);
  }

  /* ---------- 上传 + 预测 ---------- */
  function uploadAndPredict(file) {
    if (!file) return;
    if (!/image\/(jpeg|png)/.test(file.type)) {
      showToast('请上传 JPG 或 PNG 格式图片', 'warn');
      return;
    }
    if (file.size > 16 * 1024 * 1024) {
      showToast('图片超过 16MB 上限', 'warn');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      $('#originalPreview').src = e.target.result;
      currentOriginal = e.target.result;
      $('#previewContainer').classList.remove('hidden');
      $('#resultArea').classList.add('hidden');
      $('#maskPreview').style.display = 'none';
      $('#overlayCanvas').style.display = 'none';
    };
    reader.readAsDataURL(file);

    setStep(2);
    $('#loadingIndicator').classList.remove('hidden');

    const formData = new FormData();
    formData.append('image', file);

    apiFetch('/api/predict', { method: 'POST', body: formData })
      .then(renderResult)
      .catch((err) => {
        setStep(1);
        showToast(err.message || '诊断失败，请重试', 'danger');
      })
      .finally(() => $('#loadingIndicator').classList.add('hidden'));
  }

  /* ---------- 诊断报告：预览 + 导出 + 打印 ---------- */
  function renderReportPreview() {
    if (!window.__lastResult || !buildReportCard) return;
    const box = $('#reportPreview');
    if (!box) return;
    box.innerHTML = buildReportCard(window.__lastResult);
    box.classList.remove('hidden');
  }

  function doExportReport() {
    if (!window.__lastResult) { showToast('请先完成一次诊断', 'warn'); return; }
    renderReportPreview();
    showToast('诊断报告已生成，可在下方预览或继续打印', 'success');
  }

  function doPrintReport() {
    if (!window.__lastResult) { showToast('请先完成一次诊断', 'warn'); return; }
    if (printReport) printReport(buildReportCard(window.__lastResult));
  }

  /* ---------- 事件绑定 ---------- */
  function init() {
    if (!uploadArea) return;

    uploadArea.addEventListener('click', () => imageInput.click());
    imageInput.addEventListener('change', (e) => {
      if (e.target.files[0]) uploadAndPredict(e.target.files[0]);
    });

    uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadArea.classList.add('dragover');
    });
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
    uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadArea.classList.remove('dragover');
      uploadAndPredict(e.dataTransfer.files[0]);
    });

    $('#alphaSlider').addEventListener('input', () => {
      updateAlphaLabel();
      drawOverlay();
    });
    $('#maskColor').addEventListener('input', () => drawOverlay());
    $('#toggleOverlay').addEventListener('change', () => drawOverlay());

    $('#saveToHistoryBtn').addEventListener('click', () => {
      showToast('诊断结果已保存到病历本，可在「诊断档案」查看', 'success');
    });

    $('#exportReportBtn').addEventListener('click', doExportReport);
    $('#printReportBtn').addEventListener('click', doPrintReport);

    $('#newDiagnosisBtn').addEventListener('click', () => {
      $('#previewContainer').classList.add('hidden');
      $('#resultArea').classList.add('hidden');
      $('#reportPreview').classList.add('hidden');
      imageInput.value = '';
      currentOriginal = null;
      currentMask = null;
      window.__lastResult = null;
      setStep(1);
    });

    window.addEventListener('resize', () => drawOverlay());
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
