from flask import Blueprint, render_template, session, request, jsonify, redirect, url_for
from models.knowledge_base import get_all_diseases, get_categories, get_disease_by_code, get_disease_by_name
from models.database import get_user_records, add_plant_to_library, get_user_plant_library
from utils.logging_utils import log_info
 
knowledge_bp = Blueprint('knowledge', __name__)
 
@knowledge_bp.route('/knowledge')
def knowledge_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    categories = get_categories()
    return render_template('knowledge.html', categories=categories, username=session.get('username', '用户'))
 
@knowledge_bp.route('/api/diseases', methods=['GET'])
def api_get_diseases():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    category = request.args.get('category', None)
    diseases, total = get_all_diseases(page, per_page, category)
    return jsonify({'diseases': diseases, 'total': total, 'page': page, 'per_page': per_page})
 
@knowledge_bp.route('/api/disease/<int:code>')
def api_get_disease(code):
    disease = get_disease_by_code(code)
    return jsonify(disease)
 
@knowledge_bp.route('/api/disease/search')
def api_search_disease():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'results': []})
    results = []
    for info in get_all_diseases(1, 500)[0]:
        if q.lower() in info['name'].lower() or q.lower() in info['category'].lower():
            results.append(info)
    return jsonify({'results': results[:20]})
 
@knowledge_bp.route('/api/user/plants', methods=['GET', 'POST'])
def user_plants():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    if request.method == 'GET':
        plants = get_user_plant_library(user_id)
        return jsonify({'plants': plants})
    else:
        data = request.get_json()
        plant_name = data.get('plant_name', '').strip()
        plant_type = data.get('plant_type', '')
        if plant_name:
            add_plant_to_library(user_id, plant_name, plant_type)
            return jsonify({'success': True})
        return jsonify({'success': False}), 400
 
@knowledge_bp.route('/api/user/history_records')
def history_records():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    records = get_user_records(session['user_id'], limit=100)
    for r in records:
        r['created_at'] = r['created_at']
    return jsonify({'records': records})
