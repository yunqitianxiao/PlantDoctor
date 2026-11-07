from flask import Flask, render_template, send_from_directory, session, redirect, url_for, request, jsonify
import os
from config import Config
from utils.logging_utils import log_info, log_error
from models.database import init_db
from werkzeug.security import check_password_hash, generate_password_hash
from controllers.dashboard_routes import dashboard_bp
from controllers.diagnose_routes import diagnose_bp
from controllers.knowledge_routes import knowledge_bp
from controllers.frontend_routes import frontend_bp
 
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('instance', exist_ok=True)
 
init_db()
 
# 注册蓝图（不含auth_bp，因为我们直接用简单路由）
app.register_blueprint(dashboard_bp)
app.register_blueprint(diagnose_bp)
app.register_blueprint(knowledge_bp)
app.register_blueprint(frontend_bp)
 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        from models.database import get_user_by_username
        user = get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard.dashboard'))
        else:
            return render_template('login.html', error='用户名或密码错误')
    return render_template('login.html')
 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            return render_template('register.html', error='用户名和密码不能为空')
        if len(password) < 4:
            return render_template('register.html', error='密码长度至少4位')
        from models.database import get_user_by_username, create_user
        if get_user_by_username(username):
            return render_template('register.html', error='用户名已存在')
        password_hash = generate_password_hash(password)
        if create_user(username, password_hash):
            return render_template('register.html', success='注册成功！请登录')
        else:
            return render_template('register.html', error='注册失败')
    return render_template('register.html')
 
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
 
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)
 
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
 
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404
 
@app.errorhandler(500)
def internal_error(e):
    log_error(e, "500 error")
    return jsonify({'error': 'Internal server error'}), 500
 
if __name__ == '__main__':
    log_info("Starting Plant Doctor application")
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
