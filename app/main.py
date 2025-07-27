from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
from lib import *
from service import *
from database import init_databases, get_redis
import time

app = FastAPI()

# Initialize databases on startup
init_databases()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Initialize game world
    await instance_world()
    await instance_creatures()
    await instance_npcs()
    await instance_objects()
    
    # Start game loop
    asyncio.create_task(game_loop())

async def game_loop():
    """Run game ticks every 0.6 seconds"""
    redis = await get_redis()
    while True:
        start_time = time.time()
        await calculate_damages(redis)
        processing_time = time.time() - start_time
        await asyncio.sleep(max(0, 0.6 - processing_time))

# Account Endpoints
@app.post("/account/{userid}")
async def create_account_endpoint(userid: str):
    if await create_account(userid):
        return {"message": "Account created"}
    raise HTTPException(status_code=400, detail="Account already exists")

@app.post("/character")
async def create_character_endpoint(userid: str, charname: str):
    charid = await create_character(userid, charname)
    if charid:
        return {"charid": charid}
    raise HTTPException(status_code=400, detail="Character creation failed")

# Gameplay Endpoints
@app.post("/login/{charid}")
async def login_endpoint(charid: int):
    if await log_in(charid):
        return {"message": "Logged in"}
    raise HTTPException(status_code=404, detail="Character not found")

@app.post("/move/{charid}")
async def move_character_endpoint(charid: int, dx: float, dy: float):
    if await move_direction(charid, dx, dy):
        return {"message": "Movement processed"}
    raise HTTPException(status_code=404, detail="Character not found")

@app.post("/attack/{charid}")
async def attack_character_endpoint(charid: int, target_id: int):
    if await attack_direction(charid, target_id):
        return {"message": "Attack initiated"}
    raise HTTPException(status_code=404, detail="Character or target not found")

@app.post("/interact/{charid}")
async def interact_object_endpoint(charid: int, object_id: int):
    if await interact_direction(charid, object_id):
        return {"message": "Interaction initiated"}
    raise HTTPException(status_code=404, detail="Character or object not found")

@app.post("/get_info/{charid}/")
async def get_info_endpoint(charid: int, players: List[int], monsters: List[int], npcs: List[int], items: List[int]):
    r = await get_info(charid, players, monsters, npcs, items):
    return r

# Real-time Events
@app.get("/events")
async def game_events():
    async def event_stream():
        redis = await get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe("movement", "combat", "death", "interaction")
        
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is not None:
                    yield f"data: {message['data']}\n\n"
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            await pubsub.unsubscribe()
            await pubsub.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")
