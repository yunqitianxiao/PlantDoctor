from flask import Blueprint, render_template, session, jsonify, redirect, url_for
from datetime import datetime
import random
from models.database import get_user_records
from utils.logging_utils import log_info
 
dashboard_bp = Blueprint('dashboard', __name__)
 
from datetime import datetime
 
@dashboard_bp.route('/')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # 记得 import redirect
    user_id = session['user_id']
    username = session.get('username', 'User')
    recent_records = get_user_records(user_id, limit=5)
    tips = generate_daily_tips()
    weather_info = get_weather_suggestion()
    plant_stats = get_plant_statistics(user_id)
    return render_template('dashboard.html',
                          username=username,
                          recent_records=recent_records,
                          daily_tips=tips,
                          weather_info=weather_info,
                          plant_stats=plant_stats,
                          now=datetime.now().strftime('%Y-%m-%d'))
@dashboard_bp.route('/api/dashboard/stats')
def dashboard_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    records = get_user_records(user_id, limit=100)
    total_diagnoses = len(records)
    healthy_count = sum(1 for r in records if '健康' in r.get('disease_name', ''))
    disease_count = total_diagnoses - healthy_count
    severity_counts = {'mild': 0, 'moderate': 0, 'severe': 0}
    for r in records:
        level = r.get('severity_level', '')
        if level in severity_counts:
            severity_counts[level] += 1
    return jsonify({
        'total_diagnoses': total_diagnoses,
        'healthy_count': healthy_count,
        'disease_count': disease_count,
        'severity_distribution': severity_counts
    })
 
def generate_daily_tips():
    tips_list = [
        "早晨浇水可以减少蒸发，避免叶片灼伤。",
        "定期检查叶片背面，许多害虫喜欢藏在那里。",
        "每月施一次有机肥，植物会更健康。",
        "修剪枯枝病叶，保持植株通风。",
        "冬季减少浇水频率，防止烂根。",
        "新买的植物建议隔离观察一周。",
        "使用粘虫板监测飞虫数量。",
        "每两年换一次盆土，补充养分。"
    ]
    return random.choice(tips_list)
 
def get_weather_suggestion():
    hour = datetime.now().hour
    if 6 <= hour < 18:
        return {"condition": "白天", "suggestion": "适合进行叶片检查和施肥", "icon": "sun"}
    else:
        return {"condition": "夜晚", "suggestion": "避免浇水，预防夜间湿度过大", "icon": "moon"}
 
def get_plant_statistics(user_id):
    records = get_user_records(user_id, limit=100)
    plant_types = {}
    for r in records:
        name = r.get('disease_name', '未知')
        if '苹果' in name:
            plant = '苹果'
        elif '番茄' in name:
            plant = '番茄'
        elif '玉米' in name:
            plant = '玉米'
        elif '葡萄' in name:
            plant = '葡萄'
        elif '辣椒' in name:
            plant = '辣椒'
        elif '马铃薯' in name:
            plant = '马铃薯'
        elif '健康' in name:
            plant = '健康植物'
        else:
            plant = '其他'
        plant_types[plant] = plant_types.get(plant, 0) + 1
    return plant_types
