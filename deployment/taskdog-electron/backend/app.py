#!/usr/bin/env python3
"""
TaskDog Backend API
REST API for task management and WhatsApp reminder system
"""
import os
from datetime import datetime

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'taskdog-secret-key-change-in-production')

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

app = Flask(__name__, static_folder=_STATIC_DIR, static_url_path='')
app.config['SECRET_KEY'] = SECRET_KEY
CORS(app)  # Enable CORS for frontend communication

# Import routes after initializing Flask app to avoid circular imports
from routes.tasks import bp as tasks_bp
from routes.setup import bp as setup_bp
from routes.groups import bp as groups_bp
from routes.pipeline import bp as pipeline_bp
from routes.dashboard import bp as dashboard_bp
from routes.nudge import bp as nudge_bp

app.register_blueprint(tasks_bp)
app.register_blueprint(setup_bp)
app.register_blueprint(groups_bp)
app.register_blueprint(pipeline_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(nudge_bp)

# Initialize databases on startup
from models.database import init_db
init_db()

from models.database_v2 import init_db_v2
init_db_v2()

# Serve frontend static files (for Electron — no separate Vite dev server)
@app.route('/')
def serve_index():
    index_path = os.path.join(_STATIC_DIR, 'index.html')
    if os.path.isfile(index_path):
        return send_from_directory(_STATIC_DIR, 'index.html')
    return jsonify({"ok": False, "error": "Frontend not built. static/index.html missing."}), 500

@app.route('/<path:path>')
def serve_static(path):
    # Don't intercept API routes
    if path.startswith('api/'):
        return jsonify({"ok": False, "error": "Not found"}), 404
    full = os.path.join(_STATIC_DIR, path)
    if os.path.isfile(full):
        return send_from_directory(_STATIC_DIR, path)
    # SPA fallback — serve index.html for client-side routing
    index_path = os.path.join(_STATIC_DIR, 'index.html')
    if os.path.isfile(index_path):
        return send_from_directory(_STATIC_DIR, 'index.html')
    return jsonify({"ok": False, "error": "Not found"}), 404

@app.route('/health')
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

# Error handler
@app.errorhandler(404)
def not_found(error):
    return jsonify({"ok": False, "error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"ok": False, "error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=False)