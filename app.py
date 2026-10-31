from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import time

app = Flask(__name__)
CORS(app)  # This automatically allows cross-origin requests from Vercel/browsers

DB_FILE = "security_telemetry.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lockdown_sessions (
            session_id TEXT PRIMARY KEY,
            reason TEXT,
            status TEXT,
            timestamp TEXT,
            attempts INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lockdown_sessions ORDER BY timestamp DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/os-lockdown', methods=['POST'])
def trigger_lockdown():
    data = request.json or {}
    reason = data.get("reason", "Payment Manipulation")
    session_id = f"LOCK-{int(time.time())}"
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO lockdown_sessions (session_id, reason, status, timestamp, attempts) 
        VALUES (?, ?, 'ACTIVE', datetime('now', 'localtime'), 0)
    """, (session_id, reason))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "CHAOS_ENGAGED", "session_id": session_id})

@app.route('/api/lift-quarantine', methods=['GET'])
def lift_quarantine():
    session_id = request.args.get("session_id")
    if session_id:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE lockdown_sessions SET status = 'DISARMED' WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "SUCCESS", "message": f"Session {session_id} disarmed."})
    return jsonify({"status": "ERROR", "message": "Missing session_id"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
