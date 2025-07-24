from database import get_sqlite_connection, get_redis
from typing import Optional, Dict, Any
import sqlite3

# Account Tools
async def create_account(userid: str) -> bool:
    conn = get_sqlite_connection()
    try:
        conn.execute("INSERT INTO accounts (userid) VALUES (?)", (userid,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

async def create_character(userid: str, charname: str) -> Optional[int]:
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
async def log_in(charid: int) -> bool:
    conn = get_sqlite_connection()
    redis = await get_redis()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM characters WHERE charid = ?", (charid,))
        char_data = cursor.fetchone()
        
        if not char_data:
            return False
        
        # Store in Redis
        char_key = f"char:{charid}"
        await redis.hmset(char_key, {
            "x": char_data["x"],
            "y": char_data["y"],
            "health": char_data["health"],
            "max_health": char_data["max_health"],
            "state": "online"
        })
        await redis.sadd("online_chars", charid)
        return True
    finally:
        conn.close()

async def instance_world():
    """Load world state from SQLite to Redis"""
    redis = await get_redis()
    await redis.set("world:instanced", "true")

async def instance_creatures():
    """Load creatures from SQLite to Redis"""
    redis = await get_redis()
    await redis.set("creatures:instanced", "true")

async def instance_npcs():
    """Load NPCs from SQLite to Redis"""
    conn = get_sqlite_connection()
    redis = await get_redis()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT charid, name, x, y, health, max_health FROM characters WHERE userid = 'npc'")
        
        for npc in cursor.fetchall():
            npc_key = f"npc:{npc['charid']}"
            await redis.hmset(npc_key, {
                "name": npc["name"],
                "x": npc["x"],
                "y": npc["y"],
                "health": npc["health"],
                "max_health": npc["max_health"],
                "state": "idle"
            })
            await redis.sadd("npcs", npc["charid"])
        
        await redis.set("npcs:instanced", "true")
        return True
    finally:
        conn.close()

async def instance_objects():
    """Load game objects from SQLite to Redis"""
    conn = get_sqlite_connection()
    redis = await get_redis()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT object_id, name, x, y, type FROM game_objects")
        
        for obj in cursor.fetchall():
            obj_key = f"object:{obj['object_id']}"
            await redis.hmset(obj_key, {
                "name": obj["name"],
                "x": obj["x"],
                "y": obj["y"],
                "type": obj["type"],
                "state": "active"
            })
            await redis.sadd("world_objects", obj["object_id"])
        
        await redis.set("objects:instanced", "true")
        return True
    finally:
        conn.close()