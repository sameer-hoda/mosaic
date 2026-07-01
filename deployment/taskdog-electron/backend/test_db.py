import sqlite3

# Test the database directly
DATABASE_PATH = "taskdog.db"

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn

def test_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Test the queries individually
    try:
        print("Testing total query:")
        cursor.execute('SELECT COUNT(*) as total FROM tasks')
        result = cursor.fetchone()
        print(f"Result: {result}")
        print(f"Result type: {type(result)}")
        if result:
            print(f"result['total']: {result['total']}")
            print(f"list(result): {list(result)}")
        print()
        
        print("Testing sent query:")
        cursor.execute('SELECT COUNT(*) as sent FROM tasks WHERE status = "sent"')
        result = cursor.fetchone()
        print(f"Result: {result}")
        if result:
            print(f"result['sent']: {result['sent']}")
        print()
        
        print("Testing ignored query:")
        cursor.execute('SELECT COUNT(*) as ignored FROM tasks WHERE status = "ignored"')
        result = cursor.fetchone()
        print(f"Result: {result}")
        if result:
            print(f"result['ignored']: {result['ignored']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    test_stats()