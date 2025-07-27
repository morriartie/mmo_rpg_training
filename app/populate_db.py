#!/usr/bin/env python3
import sqlite3
import asyncio
import os
import pandas as pd
from pathlib import Path
from database import get_sqlite_connection, init_databases

DATA_DIR = Path("/app/data/pre_data")

async def load_all_csv_data(conn: sqlite3.Connection):
    """Load all CSV files from data directory into SQLite"""
    print(f"Loading data from {DATA_DIR}...")
    
    # Get all CSV files in data directory
    csv_files = list(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")
    
    loaded_tables = []
    
    for csv_file in csv_files:
        table_name = csv_file.stem  # Use filename without extension as table name
        try:
            df = pd.read_csv(csv_file, keep_default_na=False)
            if df.empty:
                print(f"⚠️  Empty CSV file: {csv_file.name}")
                continue
            
            # Clean column names and convert to string to prevent type issues
            df.columns = [col.strip() for col in df.columns]
            str_cols = df.select_dtypes(include=['object']).columns
            df[str_cols] = df[str_cols].astype(str)
            
            df.to_sql(
                name=table_name,
                con=conn,
                if_exists='append',
                index=False
            )
            loaded_tables.append(table_name)
            print(f"✅ Loaded {len(df)} rows into {table_name}")
            
        except Exception as e:
            print(f"❌ Failed to load {csv_file.name}: {str(e)}")
            continue
    
    return loaded_tables

async def load_to_redis(conn: sqlite3.Connection, redis):
    """Selectively load specific tables to Redis with custom logic"""
    print("\nTransferring data to Redis...")
    
    # Character/Player loading
    try:
        chars_df = pd.read_sql("SELECT * FROM characters", conn)
        if not chars_df.empty:
            pipe = redis.pipeline()
            for _, row in chars_df.iterrows():
                is_npc = row['userid'] == 'npc'
                prefix = 'npc' if is_npc else 'char'
                key = f"{prefix}:{row['charid']}"
                
                pipe.hset(key, mapping={
                    'name': str(row['name']),
                    'x': str(row['x']),
                    'y': str(row['y']),
                    'health': str(row.get('health', '')),
                    'max_health': str(row.get('max_health', '')),
                    'instance': str(row.get('instance', '')),
                    'state': 'idle' if is_npc else 'online'
                })
                
                if is_npc:
                    pipe.sadd('npcs', row['charid'])
                else:
                    pipe.sadd('online_chars', row['charid'])
            
            await pipe.execute()
            print(f"✅ Loaded {len(chars_df)} characters to Redis")
    except Exception as e:
        print(f"❌ Failed to load characters: {str(e)}")
    
    # Game Objects loading
    try:
        objects_df = pd.read_sql("SELECT * FROM game_objects", conn)
        if not objects_df.empty:
            pipe = redis.pipeline()
            for _, row in objects_df.iterrows():
                key = f"object:{row['object_id']}"
                pipe.hset(key, mapping={
                    'name': str(row['name']),
                    'x': str(row['x']),
                    'y': str(row['y']),
                    'type': str(row['type']),
                    'instance': str(row.get('instance', '')),
                    'state': 'active'
                })
                pipe.sadd('world_objects', row['object_id'])
            
            await pipe.execute()
            print(f"✅ Loaded {len(objects_df)} objects to Redis")
    except Exception as e:
        print(f"❌ Failed to load game objects: {str(e)}")
    
    # Map Instances loading
    try:
        instances_df = pd.read_sql("SELECT * FROM instances", conn)
        if not instances_df.empty:
            pipe = redis.pipeline()
            for _, row in instances_df.iterrows():
                key = f"instance:{row['instance_id']}"
                pipe.hset(key, mapping={
                    'name': str(row['name']),
                    'x_size': str(row['x_size']),
                    'y_size': str(row['y_size']),
                    'tags': str(row.get('tags', ''))
                })
                if 'height_map' in row:
                    pipe.set(f"{key}:height", str(row['height_map']))
                if 'collision_map' in row:
                    pipe.set(f"{key}:collision", str(row['collision_map']))
            
            await pipe.execute()
            print(f"✅ Loaded {len(instances_df)} instances to Redis")
    except Exception as e:
        print(f"❌ Failed to load instances: {str(e)}")
    
    # Set world metadata
    await redis.set("world:instanced", "true")
    print("✅ Set world metadata in Redis")

async def main():
    # Initialize database structure
    init_databases()
    
    # Connect to databases
    conn = get_sqlite_connection()
    redis = await get_redis()
    
    try:
        # Development mode - clear existing data
        if os.getenv('ENV') == 'development':
            await redis.flushdb()
            print("Cleared Redis for development mode")
        
        # Load all CSV data into SQLite
        loaded_tables = await load_all_csv_data(conn)
        conn.commit()
        
        if not loaded_tables:
            raise RuntimeError("No tables were loaded from CSV files")
        
        # Transfer specific tables to Redis
        await load_to_redis(conn, redis)
        
        print("\nDatabase population complete!")
        print(f"Loaded tables: {', '.join(loaded_tables)}")
    
    except Exception as e:
        conn.rollback()
        print(f"Critical error: {str(e)}")
        raise
    
    finally:
        conn.close()
        await redis.close()

if __name__ == "__main__":
    asyncio.run(main())
