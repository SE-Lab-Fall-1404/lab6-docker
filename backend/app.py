from flask import Flask, request, jsonify, make_response
import psycopg2
import os
import socket
import time
from psycopg2.extras import RealDictCursor
from psycopg2 import OperationalError

app = Flask(__name__)

def get_db_connection(max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'db'),
                database=os.environ.get('DB_NAME', 'mydb'),
                user=os.environ.get('DB_USER', 'myuser'),
                password=os.environ.get('DB_PASSWORD', 'mypassword'),
                connect_timeout=5
            )
            return conn
        except OperationalError as e:
            retries += 1
            print(f"Database connection failed. Attempt {retries} of {max_retries}")
            time.sleep(3)
    raise Exception("Failed to connect to database after 5 attempts")

def init_db():
    """Create items table in the database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Items table created or verified successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

# Initialize database on startup
print("🔄 Initializing database...")
init_db()

@app.route('/')
def index():
    return jsonify({
        'service': 'Backend API',
        'hostname': socket.gethostname(),
        'status': 'running',
        'database': 'connected'
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'hostname': socket.gethostname()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'hostname': socket.gethostname()
        }), 500

@app.route('/items', methods=['GET'])
def get_items():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM items ORDER BY id')
        items = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items', methods=['POST'])
def create_item():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request must contain JSON'}), 400
        
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Item name is required'}), 400
        
        description = data.get('description', '')
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            'INSERT INTO items (name, description) VALUES (%s, %s) RETURNING id, name, description',
            (name, description)
        )
        item = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(item), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items/<int:id>', methods=['GET'])
def get_item(id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM items WHERE id = %s', (id,))
        item = cur.fetchone()
        cur.close()
        conn.close()
        if item:
            return jsonify(item)
        return make_response(jsonify({'error': 'Item not found'}), 404)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items/<int:id>', methods=['PUT'])
def update_item(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request must contain JSON'}), 400
        
        name = data.get('name')
        description = data.get('description')
        
        # Build dynamic query based on provided fields
        updates = []
        values = []
        if name is not None:
            updates.append("name = %s")
            values.append(name)
        if description is not None:
            updates.append("description = %s")
            values.append(description)
        
        if not updates:
            return jsonify({'error': 'At least one field to update is required'}), 400
        
        values.append(id)
        query = f"UPDATE items SET {', '.join(updates)} WHERE id = %s RETURNING *"
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, tuple(values))
        updated_item = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if updated_item:
            return jsonify(updated_item)
        return make_response(jsonify({'error': 'Item not found'}), 404)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/items/<int:id>', methods=['DELETE'])
def delete_item(id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM items WHERE id = %s', (id,))
        conn.commit()
        rowcount = cur.rowcount
        cur.close()
        conn.close()
        
        if rowcount > 0:
            return jsonify({'message': 'Item deleted successfully'})
        return make_response(jsonify({'error': 'Item not found'}), 404)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset_database():
    """Reset the items table (for testing only)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DROP TABLE IF EXISTS items')
        cur.execute('''
            CREATE TABLE items (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Table reset successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Flask server starting...")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)