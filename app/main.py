from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from lib import *
from service import *
from database import init_databases

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
    instance_world()
    instance_creatures()
    instance_npcs()
    instance_objects()
    
    # Start game loop
    asyncio.create_task(game_loop())

async def game_loop():
    """Run game ticks every 0.6 seconds"""
    while True:
        game_tick()
        await asyncio.sleep(0.6)

# Account Endpoints
@app.post("/account/{userid}")
def create_account_endpoint(userid: str):
    if create_account(userid):
        return {"message": "Account created"}
    raise HTTPException(status_code=400, detail="Account already exists")

@app.post("/character")
def create_character_endpoint(userid: str, charname: str):
    charid = create_character(userid, charname)
    if charid:
        return {"charid": charid}
    raise HTTPException(status_code=400, detail="Character creation failed")

# Gameplay Endpoints
@app.post("/login/{charid}")
def login_endpoint(charid: int):
    if log_in(charid):
        return {"message": "Logged in"}
    raise HTTPException(status_code=404, detail="Character not found")

@app.post("/move/{charid}")
def move_character_endpoint(charid: int, dx: float, dy: float):
    if move_direction(charid, dx, dy):
        return {"message": "Movement processed"}
    raise HTTPException(status_code=404, detail="Character not found")

@app.post("/attack/{charid}")
def attack_character_endpoint(charid: int, target_id: int):
    if attack_direction(charid, target_id):
        return {"message": "Attack initiated"}
    raise HTTPException(status_code=404, detail="Character or target not found")

@app.post("/interact/{charid}")
def interact_object_endpoint(charid: int, object_id: int):
    if interact_direction(charid, object_id):
        return {"message": "Interaction initiated"}
    raise HTTPException(status_code=404, detail="Character or object not found")

# Real-time Events
@app.get("/events")
async def game_events():
    pubsub = redis_conn.pubsub()
    pubsub.subscribe("movement", "combat", "death", "interaction")
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            yield f"data: {message['data']}\n\n"
