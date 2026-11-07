import sqlite3
import json
from datetime import datetime
from config import Config
from utils.logging_utils import handle_exceptions, log_info, log_error
 
def get_db():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn
 
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diagnosis_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            image_path TEXT,
            disease_name TEXT NOT NULL,
            disease_code INTEGER,
            severity_ratio REAL,
            severity_level TEXT,
            confidence REAL,
            treatment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            recovery_status TEXT DEFAULT 'pending',
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plant_knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disease_name TEXT UNIQUE NOT NULL,
            disease_code INTEGER,
            category TEXT,
            symptoms TEXT,
            causes TEXT,
            treatment TEXT,
            prevention TEXT,
            image_url TEXT,
            severity_guide TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_plant_library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plant_name TEXT,
            plant_type TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()
    log_info("Database initialized")
 
@handle_exceptions(default_return=False)
def save_diagnosis_record(user_id, image_path, disease_name, disease_code, severity_ratio, severity_level, confidence, treatment):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO diagnosis_records 
        (user_id, image_path, disease_name, disease_code, severity_ratio, severity_level, confidence, treatment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, image_path, disease_name, disease_code, severity_ratio, severity_level, confidence, treatment))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    log_info(f"Saved diagnosis record {record_id} for user {user_id}")
    return record_id
 
@handle_exceptions(default_return=[])
def get_user_records(user_id, limit=50):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, disease_name, severity_level, confidence, treatment, created_at, recovery_status, image_path
        FROM diagnosis_records 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
 
@handle_exceptions(default_return=False)
def update_recovery_status(record_id, status):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE diagnosis_records SET recovery_status = ? WHERE id = ?', (status, record_id))
    conn.commit()
    conn.close()
    return True
 
@handle_exceptions(default_return=False)
def delete_record(record_id, user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM diagnosis_records WHERE id = ? AND user_id = ?', (record_id, user_id))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0
 
@handle_exceptions(default_return=None)
def get_user_by_username(username):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None
 
@handle_exceptions(default_return=False)
def create_user(username, password_hash):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
    conn.commit()
    conn.close()
    return True
 
@handle_exceptions(default_return=False)
def add_plant_to_library(user_id, plant_name, plant_type):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO user_plant_library (user_id, plant_name, plant_type) VALUES (?, ?, ?)',
                   (user_id, plant_name, plant_type))
    conn.commit()
    conn.close()
    return True
 
@handle_exceptions(default_return=[])
def get_user_plant_library(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, plant_name, plant_type, added_at FROM user_plant_library WHERE user_id = ? ORDER BY added_at DESC', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
