from .database import redis_conn
import json
import time

# Runtime Tools
def move_direction(charid: int, dx: float, dy: float) -> bool:
    char_key = f"char:{charid}"
    if not redis_conn.exists(char_key):
        return False
    
    # Get current position
    x = float(redis_conn.hget(char_key, "x"))
    y = float(redis_conn.hget(char_key, "y"))
    
    # Update position
    new_x = x + dx
    new_y = y + dy
    
    # Collision check
    if not detect_collision(new_x, new_y):
        redis_conn.hset(char_key, "x", new_x)
        redis_conn.hset(char_key, "y", new_y)
        redis_conn.publish("movement", json.dumps({
            "charid": charid,
            "x": new_x,
            "y": new_y
        }))
        return True
    return False

def attack_direction(charid: int, target_id: int) -> bool:
    char_key = f"char:{charid}"
    target_key = f"char:{target_id}"  # Could be player or NPC
    
    if not redis_conn.exists(char_key) or not redis_conn.exists(target_key):
        return False
    
    # Add to combat queue
    redis_conn.rpush("combat_queue", json.dumps({
        "attacker": charid,
        "target": target_id,
        "time": time.time()
    }))
    return True

def interact_direction(charid: int, object_id: int) -> bool:
    char_key = f"char:{charid}"
    object_key = f"object:{object_id}"
    
    if not redis_conn.exists(char_key) or not redis_conn.exists(object_key):
        return False
    
    # Add to interaction queue
    redis_conn.rpush("interaction_queue", json.dumps({
        "charid": charid,
        "object_id": object_id,
        "time": time.time()
    }))
    return True

# Systems
def detect_collision(x: float, y: float) -> bool:
    """Check collision with world objects"""
    # Placeholder implementation
    return False

def calculate_damages():
    """Process combat queue on game tick"""
    while redis_conn.llen("combat_queue") > 0:
        combat_data = json.loads(redis_conn.lpop("combat_queue"))
        attacker_id = combat_data["attacker"]
        target_id = combat_data["target"]
        
        target_key = f"char:{target_id}"
        target_key = f"char:{target_id}" if redis_conn.exists(f"char:{target_id}") else f"npc:{target_id}"
        
        if not redis_conn.exists(target_key):
            continue
        
        # Calculate damage
        damage = 10  # Base damage
        
        # Apply damage
        current_health = int(redis_conn.hget(target_key, "health"))
        new_health = max(0, current_health - damage)
        redis_conn.hset(target_key, "health", new_health)
        
        # Publish combat event
        target_type = "char" if "char:" in target_key else "npc"
        redis_conn.publish("combat", json.dumps({
            "attacker": attacker_id,
            "target": target_id,
            "target_type": target_type,
            "damage": damage,
            "new_health": new_health
        })) 

        # Check for death
        if new_health <= 0:
            redis_conn.hset(target_key, "state", "dead")
            redis_conn.publish("death", json.dumps({
                "charid": target_id,
                "killer": attacker_id
            }))

def calculate_movements():
    """Process movement queues (if any)"""
    # Could implement pathfinding here
    pass

def game_tick():
    """Process one game tick (0.6s)"""
    calculate_damages()
    calculate_movements()
    # Other systems would be called here
