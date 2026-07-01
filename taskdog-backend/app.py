#!/usr/bin/env python3
"""
TaskDog Backend API
REST API for task management and WhatsApp reminder system
"""
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify
from flask_cors import CORS

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'taskdog-secret-key-change-in-production')

app = Flask(__name__)
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

# Default route
@app.route('/')
def index():
    return jsonify({
        "message": "TaskDog Backend API",
        "version": "1.0.0",
        "endpoints": [
            "GET /api/tasks",
            "POST /api/send",
            "POST /api/ignore",
            "POST /api/login"
        ]
    })

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
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='127.0.0.1', port=3001, debug=debug)