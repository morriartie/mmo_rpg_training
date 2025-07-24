import sqlite3
from redis.asyncio import Redis  # Updated import
import os
from typing import Optional

# SQLite connection
def get_sqlite_connection():
    db_path = os.getenv('DB_PATH', '/data/world.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Redis connection handling
_redis: Optional[Redis] = None

async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(
            "redis://redis",
            decode_responses=True
        )
    return _redis

async def close_redis():
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None

def init_databases():
    """Initialize both SQLite and Redis databases"""
    # Initialize SQLite
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
