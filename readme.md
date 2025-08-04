# Sports Data API

Features:
- RESTful API for live scores, player stats, and team rankings.
- Caching with Redis to handle 10,000+ RPM (requests per minute).
- Rate limiting (100 requests/minute) and Swagger documentation.

## Endpoints

### `GET /live-scores`
Returns the latest game scores. Data is cached for 30 seconds.

```
{
  "data": {
    "games": [
      {"home": "Team A", "away": "Team B", "score": "89-86"},
      {"home": "Team C", "away": "Team D", "score": "102-99"}
    ]
  },
  "source": "API"
}
```

### `GET /player-stats/{player_id}`
Retrieve statistics for a specific player.

```
GET /player-stats/23

{
  "data": {"id": "23", "points": 25, "assists": 5},
  "source": "API"
}
```

### `GET /team-rankings`
Fetch the current team rankings.

```
{
  "data": {
    "teams": [
      {"name": "Team A", "rank": 1},
      {"name": "Team B", "rank": 2}
    ]
  },
  "source": "API"
}
```

### `WS /ws/live-scores`
WebSocket endpoint that streams live score updates every few seconds.

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/live-scores");
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

## Running

Start the API and Redis using Docker Compose:

```
docker-compose up
```

