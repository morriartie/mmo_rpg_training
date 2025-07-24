#!/usr/bin/env python3
import sqlite3
from redis.asyncio import Redis
import asyncio
from database import get_sqlite_connection, init_databases

async def create_sample_data():
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Create sample accounts
    accounts = [
        ("player1",),
        ("player2",),
        ("adventurer",),
        ("mage",),
        ("warrior",)
    ]
    cursor.executemany("INSERT OR IGNORE INTO accounts (userid) VALUES (?)", accounts)
    
    # Create sample characters
    characters = [
        (1, "player1", "Arthas", 100.0, 200.0, 100, 100),
        (2, "player2", "Jaina", 150.0, 250.0, 80, 80),
        (3, "adventurer", "Thrall", 200.0, 300.0, 120, 120),
        (4, "mage", "Medivh", 250.0, 350.0, 70, 70),
        (5, "warrior", "Garrosh", 300.0, 400.0, 150, 150)
    ]
    cursor.executemany(
        """INSERT OR IGNORE INTO characters 
        (charid, userid, name, x, y, health, max_health) 
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        characters
    )
    
    # Create sample NPCs
    npcs = [
        (1000, "npc", "Goblin", 500.0, 500.0, 50, 50),
        (1001, "npc", "Dragon", 600.0, 600.0, 500, 500),
        (1002, "npc", "Merchant", 700.0, 700.0, 100, 100)
    ]
    cursor.executemany(
        """INSERT OR IGNORE INTO characters 
        (charid, userid, name, x, y, health, max_health) 
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        npcs
    )
    
    # Create game objects
    objects = [
        (2001, "Tree", 400.0, 400.0, "resource"),
        (2002, "Rock", 450.0, 450.0, "resource"),
        (2003, "Chest", 800.0, 800.0, "container")
    ]
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS game_objects (
            object_id INTEGER PRIMARY KEY,
            name TEXT,
            x REAL,
            y REAL,
            type TEXT
        )"""
    )
    cursor.executemany(
        "INSERT OR IGNORE INTO game_objects VALUES (?, ?, ?, ?, ?)",
        objects
    )
    
    conn.commit()
    conn.close()
    print("Created sample data in SQLite")

async def load_data_to_redis():
    redis = Redis.from_url("redis://redis", decode_responses=True)
    
    # Load characters to Redis
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Player characters
    cursor.execute("SELECT charid, x, y, health, max_health FROM characters WHERE userid != 'npc'")
    for char in cursor.fetchall():
        char_key = f"char:{char[0]}"
        await redis.hset(char_key, mapping={
            "x": char[1],
            "y": char[2],
            "health": char[3],
            "max_health": char[4],
            "state": "online"
        })
        await redis.sadd("online_chars", char[0])
    
    # NPCs
    cursor.execute("SELECT charid, x, y, health, max_health FROM characters WHERE userid = 'npc'")
    for npc in cursor.fetchall():
        npc_key = f"npc:{npc[0]}"
        await redis.hset(npc_key, mapping={
            "x": npc[1],
            "y": npc[2],
            "health": npc[3],
            "max_health": npc[4],
            "state": "idle"
        })
        await redis.sadd("npcs", npc[0])
    
    # Game objects
    cursor.execute("SELECT object_id, name, x, y, type FROM game_objects")
    for obj in cursor.fetchall():
        obj_key = f"object:{obj[0]}"
        await redis.hset(obj_key, mapping={
            "name": obj[1],
            "x": obj[2],
            "y": obj[3],
            "type": obj[4],
            "state": "active"
        })
        await redis.sadd("world_objects", obj[0])
    
    # Set world as instanced
    await redis.set("world:instanced", "true")
    await redis.set("npcs:instanced", "true")
    await redis.set("objects:instanced", "true")
    
    conn.close()
    await redis.close()
    print("Loaded data to Redis")

async def main():
    # Initialize database structure
    init_databases()
    
    # Create sample data
    await create_sample_data()
    await load_data_to_redis()
    print("Database population complete!")

if __name__ == "__main__":
    asyncio.run(main())