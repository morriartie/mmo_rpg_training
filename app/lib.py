from .database import get_sqlite_connection, redis_conn
from typing import Optional, Dict, Any

# Account Tools
def create_account(userid: str) -> bool:
    conn = get_sqlite_connection()
    try:
        conn.execute("INSERT INTO accounts (userid) VALUES (?)", (userid,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def create_character(userid: str, charname: str) -> Optional[int]:
    conn = get_sqlite_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO characters (userid, name) VALUES (?, ?)",
            (userid, charname)
        )
        charid = cursor.lastrowid
        conn.commit()
        return charid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

# Instancing Tools
def log_in(charid: int) -> bool:
    conn = get_sqlite_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM characters WHERE charid = ?", (charid,))
        char_data = cursor.fetchone()
        
        if not char_data:
            return False
        
        # Store in Redis
        char_key = f"char:{charid}"
        redis_conn.hmset(char_key, {
            "x": char_data["x"],
            "y": char_data["y"],
            "health": char_data["health"],
            "max_health": char_data["max_health"],
            "state": "online"
        })
        redis_conn.sadd("online_chars", charid)
        return True
    finally:
        conn.close()

def instance_world():
    """Load world state from SQLite to Redis"""
    # This would load terrain, static objects, etc.
    redis_conn.set("world:instanced", "true")

def instance_creatures():
    """Load creatures from SQLite to Redis"""
    # Placeholder implementation
    redis_conn.set("creatures:instanced", "true")

def instance_npcs():
    """Load NPCs from SQLite to Redis"""
    redis_conn.set("npcs:instanced", "true")

def instance_objects():
    """Load game objects from SQLite to Redis"""
    redis_conn.set("objects:instanced", "true")

def instance_npcs():
    """Load NPCs from SQLite to Redis"""
    conn = get_sqlite_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT charid, name, x, y, health, max_health FROM characters WHERE userid = 'npc'")
        
        for npc in cursor.fetchall():
            npc_key = f"npc:{npc[0]}"
            redis_conn.hmset(npc_key, {
                "name": npc[1],
                "x": npc[2],
                "y": npc[3],
                "health": npc[4],
                "max_health": npc[5],
                "state": "idle"
            })
            redis_conn.sadd("npcs", npc[0])
        
        redis_conn.set("npcs:instanced", "true")
        return True
    finally:
        conn.close()
