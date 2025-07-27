from database import get_redis
import json
import time
import asyncio
from typing import Optional

async def get_info(charid: int, characters: List[int], npcs: List[int], items: List[int]):
    elements = {"characters": {}, "npcs": {}, "items": {}}
    redis = await get_redis()
    char_key = f"char:{charid}"

    player_instance = await redis.hget(char_key, "instance")
    if not player_instance:
        return {"status": False, "message": "Character does not exist or has no instance"}

    # {"char:0000": ("characters",0000)}
    entity_map = {f"char:{id}": ("characters", id) for id in characters}
    entity_map.update({f"npc:{id}": ("npcs", id) for id in npcs})
    entity_map.update({f"object:{id}": ("items", id) for id in items})
    
    all_keys = list(entity_map.keys())
    
    pipeline = redis.pipeline()
    for key in all_keys:
        pipeline.hget(key, "instance")
    instances = await pipeline.execute()
    
    valid_keys = []
    for key, instance_val in zip(all_keys, instances):
        if instance_val and instance_val.decode() == player_instance.decode():
            valid_keys.append(key)
    
    if not valid_keys:
        return {"status": True, "elements": elements}
    
    pipeline = redis.pipeline()
    for key in valid_keys:
        pipeline.hgetall(key)
    results = await pipeline.execute()
    
    for key, data in zip(valid_keys, results):
        category, entity_id = entity_map[key]
        elements[category][entity_id] = {k.decode(): v.decode() for k, v in data.items()}
    
    return {"status": True, "elements": elements}

async def char_has_vision(char_key, target_key): # inneficient, not for batch usage
    if not redis.exists(char_key) or not redis.exists(target_key):
        return False

    char_data = await redis.hgetall(char_key)
    target_data = await redis.hgetall(target_key)

    char_instance = char_data.get("instance", False)
    if not char_instance:
        return False
    target_instance = target_data.get("instance", False)
    if target_instance == char_instance:
        return True
    return False

# Runtime Tools
async def move_direction(charid: int, dx: float, dy: float) -> bool:
    char_key = f"char:{charid}"
    redis = await get_redis()
    if not await redis.exists(char_key):
        return False
    
    # Get current position
    char_data = await redis.hgetall(char_key)
    x = float(char_data.get("x", 0))
    y = float(char_data.get("y", 0))
    
    # Update position
    new_x = x + dx
    new_y = y + dy
    
    # Collision check
    if not await detect_collision(new_x, new_y):
        await redis.hset(char_key, mapping={
            "x": new_x,
            "y": new_y
        })
        await redis.publish("movement", json.dumps({
            "charid": charid,
            "x": new_x,
            "y": new_y
        }))
        return True
    return False

async def attack_direction(charid: int, target_id: int) -> bool:
    redis = await get_redis()
    char_key = f"char:{charid}"
    target_key = f"char:{target_id}"  # Could be player or NPC
    
    if not (await redis.exists(char_key) and await redis.exists(target_key)):
        return False
    
    # Add to combat queue
    await redis.rpush("combat_queue", json.dumps({
        "attacker": charid,
        "target": target_id,
        "time": time.time()
    }))
    return True

async def interact_direction(charid: int, object_id: int) -> bool:
    redis = await get_redis()
    char_key = f"char:{charid}"
    object_key = f"object:{object_id}"
    
    if not (await redis.exists(char_key) and await redis.exists(object_key)):
        return False
    
    # Add to interaction queue
    await redis.rpush("interaction_queue", json.dumps({
        "charid": charid,
        "object_id": object_id,
        "time": time.time()
    }))
    return True

# Systems
async def detect_collision(x: float, y: float) -> bool:
    """Check collision with world objects"""
    # Placeholder implementation
    return False

async def calculate_damages(redis):  # Now accepts redis parameter
    """Process combat queue on game tick"""
    while await redis.llen("combat_queue") > 0:
        combat_data = json.loads(await redis.lpop("combat_queue"))
        attacker_id = combat_data["attacker"]
        target_id = combat_data["target"]
        
        # Determine target type
        target_key = f"char:{target_id}" if await redis.exists(f"char:{target_id}") else f"npc:{target_id}"
        
        if not await redis.exists(target_key):
            continue
        
        # Calculate damage
        damage = 10  # Base damage
        
        # Apply damage
        current_health = int(await redis.hget(target_key, "health"))
        new_health = max(0, current_health - damage)
        await redis.hset(target_key, "health", new_health)
        
        # Publish combat event
        target_type = "char" if "char:" in target_key else "npc"
        await redis.publish("combat", json.dumps({
            "attacker": attacker_id,
            "target": target_id,
            "target_type": target_type,
            "damage": damage,
            "new_health": new_health
        }))
        
        # Check for death
        if new_health <= 0:
            await redis.hset(target_key, "state", "dead")
            await redis.publish("death", json.dumps({
                "target": target_id,
                "target_type": target_type,
                "killer": attacker_id
            }))

async def calculate_movements(redis):  # Now accepts redis parameter
    """Process movement queues (if any)"""
    pass

async def game_tick(redis):  # Now accepts redis parameter
    """Process one game tick (0.6s)"""
    await calculate_damages(redis)
    await calculate_movements(redis)
