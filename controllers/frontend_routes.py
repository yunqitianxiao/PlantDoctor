from flask import Blueprint, render_template, session, redirect, url_for

frontend_bp = Blueprint('frontend', __name__)


@frontend_bp.route('/history')
def history_page():
    """诊断档案页：数据由 history.js 读取 /api/user/history_records 渲染"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('history.html', username=session.get('username', '用户'))


@frontend_bp.route('/plants')
def plants_page():
    """我的植物页：数据由 plants.js 读取 /api/user/plants 渲染"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('plants.html', username=session.get('username', '用户'))


@frontend_bp.route('/detect-batch')
def detect_batch_page():
    """批量检测页：前端逐张调用 /api/predict"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('detect_batch.html', username=session.get('username', '用户'))


@frontend_bp.route('/about')
def about_page():
    """系统说明页（公开访问）"""
    return render_template('about.html', username=session.get('username', '用户'))
