# main.py
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from dotenv import load_dotenv
import asyncio
import os
from typing import List

load_dotenv()
app = FastAPI()
redis = Redis(host="redis", port=6379, decode_responses=True)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                self.disconnect(connection)


manager = ConnectionManager()

# Rate limiting middleware
@app.middleware("http")
async def rate_limit(request, call_next):
    client_ip = request.client.host
    requests = redis.incr(client_ip)
    if requests > 100:
        raise HTTPException(status_code=429, detail="Too many requests.")
    return await call_next(request)

@app.get("/live-scores")
async def get_live_scores():
    cached_data = redis.get("live_scores")
    if cached_data:
        return {"data": cached_data, "source": "cache"}
    # Fetch from external API (mock)
    live_data = {
        "games": [
            {"home": "Team A", "away": "Team B", "score": "89-86"},
            {"home": "Team C", "away": "Team D", "score": "102-99"},
        ]
    }
    redis.setex("live_scores", 30, live_data)  # Cache for 30s
    return {"data": live_data, "source": "API"}


@app.get("/player-stats/{player_id}")
async def get_player_stats(player_id: str):
    cache_key = f"player_stats:{player_id}"
    cached_data = redis.get(cache_key)
    if cached_data:
        return {"data": cached_data, "source": "cache"}
    # Fetch from external API (mock)
    stats = {"id": player_id, "points": 25, "assists": 5}
    redis.setex(cache_key, 30, stats)
    return {"data": stats, "source": "API"}


@app.get("/team-rankings")
async def get_team_rankings():
    cached_data = redis.get("team_rankings")
    if cached_data:
        return {"data": cached_data, "source": "cache"}
    # Fetch from external API (mock)
    rankings = {
        "teams": [
            {"name": "Team A", "rank": 1},
            {"name": "Team B", "rank": 2},
        ]
    }
    redis.setex("team_rankings", 30, rankings)
    return {"data": rankings, "source": "API"}


@app.on_event("startup")
async def start_broadcast() -> None:
    asyncio.create_task(broadcast_live_scores())


async def broadcast_live_scores() -> None:
    while True:
        data = await get_live_scores()
        await manager.broadcast(data)
        await asyncio.sleep(5)


@app.websocket("/ws/live-scores")
async def websocket_live_scores(websocket: WebSocket) -> None:
    client_ip = websocket.client.host
    requests = redis.incr(client_ip)
    if requests > 100:
        await websocket.close(code=1008)
        return
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
