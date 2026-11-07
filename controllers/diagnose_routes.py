from flask import Blueprint, request, jsonify, session, current_app, render_template
import uuid
import os
import base64
from datetime import datetime
from models.model_loader import async_predictor, ModelManager
from models.database import save_diagnosis_record, get_user_records
from models.knowledge_base import get_disease_by_name
from utils.image_utils import allowed_file, calculate_severity, create_overlay_mask, resize_image
from utils.logging_utils import log_info, log_error
from config import Config
from langchain_openai import ChatOpenAI
 
diagnose_bp = Blueprint('diagnose', __name__)


def get_llm():
    """Create the LLM client lazily so the app still starts without an API key."""
    if not Config.DEEPSEEK_API_KEY:
        return None
    return ChatOpenAI(
        model=Config.DEEPSEEK_MODEL,
        openai_api_key=Config.DEEPSEEK_API_KEY,
        openai_api_base=Config.DEEPSEEK_API_BASE,
        temperature=0.6,
    )
 
from flask import Blueprint, request, jsonify, session, current_app, render_template, redirect, url_for
 
@diagnose_bp.route('/diagnose')
def diagnose_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('diagnose.html', username=session.get('username', '用户'))
 
@diagnose_bp.route('/api/predict', methods=['POST'])
def predict():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': '请先登录'}), 401
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '未上传图片'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': '未选择文件'}), 400
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': '仅支持 JPG/PNG 格式'}), 400
    try:
        image_bytes = file.read()
        task_id = str(uuid.uuid4())
        async_predictor.predict_async(task_id, image_bytes)
        success, result = async_predictor.get_result(task_id, timeout=10)
        if not success:
            return jsonify({'success': False, 'error': f'模型推理失败: {result}'}), 500
        disease_name, confidence, class_idx, mask_np = result
        if mask_np is None:
            severity_ratio = 0.0
            severity_level = 'healthy'
        else:
            severity_ratio, severity_level = calculate_severity(mask_np, (384, 384))
        disease_info = get_disease_by_name(disease_name)
        if disease_info:
            base_treatment = disease_info.get('treatment', '请咨询专业农艺师')
        else:
            base_treatment = '请咨询专业农艺师'
        enhanced_treatment = generate_enhanced_treatment(disease_name, severity_level, severity_ratio, base_treatment)
        user_id = session['user_id']
        original_filename = f"orig_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task_id[:8]}.jpg"
        original_path = os.path.join(current_app.config['UPLOAD_FOLDER'], original_filename)
        with open(original_path, 'wb') as f:
            f.write(image_bytes)
        record_id = save_diagnosis_record(user_id, original_path, disease_name, class_idx, severity_ratio, severity_level, confidence, enhanced_treatment)
        original_b64 = base64.b64encode(image_bytes).decode('utf-8')
        mask_b64 = None
        raw_mask_b64 = None
        if mask_np is not None:
            import cv2
            import numpy as np
            nparr = np.frombuffer(image_bytes, np.uint8)
            orig_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if orig_img is not None:
                orig_img = resize_image(orig_img)
                overlay = create_overlay_mask(orig_img, mask_np, alpha=0.5)
                _, buffer = cv2.imencode('.jpg', overlay)
                mask_b64 = base64.b64encode(buffer).decode('utf-8')
                # 生成透明底病灶掩码（前端可实时调节透明度/颜色）
                h, w = mask_np.shape[:2]
                rgba = np.zeros((h, w, 4), dtype=np.uint8)
                lesion = mask_np > 0
                rgba[lesion] = [46, 125, 100, 255]   # BGRA 绿色, 病灶处不透明
                _, png_buffer = cv2.imencode('.png', rgba)
                raw_mask_b64 = base64.b64encode(png_buffer).decode('utf-8')
        return jsonify({
            'success': True,
            'disease_name': disease_name,
            'confidence': confidence,
            'severity_ratio': round(severity_ratio * 100, 2),
            'severity_level': severity_level,
            'treatment': enhanced_treatment,
            'record_id': record_id,
            'original_image': f"data:image/jpeg;base64,{original_b64}",
            'mask_image': f"data:image/jpeg;base64,{mask_b64}" if mask_b64 else None,
            'raw_mask_image': f"data:image/png;base64,{raw_mask_b64}" if raw_mask_b64 else None
        })
    except Exception as e:
        log_error(e, "Prediction endpoint")
        return jsonify({'success': False, 'error': str(e)}), 500
 
def generate_enhanced_treatment(disease_name, severity_level, severity_ratio, base_treatment):
    try:
        llm = get_llm()
        if llm is None:
            return base_treatment + f"\n【严重程度: {severity_level}】请根据实际情况调整用药频率。"
        prompt = f"""病害: {disease_name}
严重程度: {severity_level} (病灶占比 {severity_ratio:.1f}%)
建议治疗方案: {base_treatment}
请根据严重程度给出分级治疗建议:
- 轻度: 预防措施
- 中度: 针对性治疗
- 重度: 紧急处理
输出简洁中文，不超过200字。"""
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        log_error(e, "LLM treatment generation")
        return base_treatment + f"\n【严重程度: {severity_level}】请根据实际情况调整用药频率。"
 
@diagnose_bp.route('/api/history', methods=['GET'])
def get_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    records = get_user_records(user_id, limit=50)
    for r in records:
        r['created_at'] = r['created_at']
    return jsonify({'records': records})
 
@diagnose_bp.route('/api/record/<int:record_id>/update_status', methods=['POST'])
def update_record_status(record_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    status = data.get('status')
    from models.database import update_recovery_status
    if update_recovery_status(record_id, status):
        return jsonify({'success': True})
    return jsonify({'success': False}), 400
 
@diagnose_bp.route('/api/record/<int:record_id>/delete', methods=['DELETE'])
def delete_record(record_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    from models.database import delete_record
    if delete_record(record_id, session['user_id']):
        return jsonify({'success': True})
    return jsonify({'success': False}), 400
