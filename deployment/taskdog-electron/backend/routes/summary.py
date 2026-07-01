from flask import Blueprint, jsonify

bp = Blueprint('summary', __name__, url_prefix='/api')

@bp.route('/summary', methods=['GET'])
def get_summary():
    try:
        from models.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get executed orders (sent tasks in last 7 days)
        cursor.execute('''
            SELECT title FROM tasks 
            WHERE status = 'sent' 
            AND updated_at >= date('now', '-7 days')
            ORDER BY updated_at DESC
        ''')
        executed_orders = [row['title'] for row in cursor.fetchall()]
        
        # Get blockers (high urgency pending tasks)
        cursor.execute('''
            SELECT title FROM tasks 
            WHERE urgency LIKE '%High%' 
            AND status = 'pending'
            ORDER BY created_at DESC
        ''')
        blockers = [row['title'] for row in cursor.fetchall()]
        
        conn.close()
        
        data = {
            "rating": 1, # Placeholder for now
            "what_got_done": executed_orders,
            "blocked_on": blockers
        }
        return jsonify(data)
        
    except Exception as e:
        print(f"Error in get_summary: {e}")
        return jsonify({
            "rating": 1,
            "what_got_done": [],
            "blocked_on": ["Error fetching data"]
        })
