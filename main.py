# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()
redis = Redis(host="redis", port=6379, decode_responses=True)

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
    live_data = {"games": [...]}
    redis.setex("live_scores", 30, live_data)  # Cache for 30s
    return {"data": live_data, "source": "API"}
