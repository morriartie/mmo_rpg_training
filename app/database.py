import sqlite3
import redis
import os


def get_sqlite_connection():
    # Use persistent storage in Docker
    db_path = os.getenv('DB_PATH', '/data/world.db') 
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Redis connection
redis_conn = redis.Redis(host='redis', port=6379, decode_responses=True)

# Initialize databases
def init_databases():
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            userid TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            charid INTEGER PRIMARY KEY,
            userid TEXT,
            name TEXT UNIQUE,
            x REAL DEFAULT 0.0,
            y REAL DEFAULT 0.0,
            health INTEGER DEFAULT 100,
            max_health INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(userid) REFERENCES accounts(userid)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_objects (
            object_id INTEGER PRIMARY KEY,
            name TEXT,
            x REAL,
            y REAL,
            type TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
