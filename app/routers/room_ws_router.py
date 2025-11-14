# app/routers/room_ws_router.py

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
import json, asyncio
from app.core.redis_client import redis_client
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.repositories.room_repo import RoomRepository
from app.core.auth_middleware import verify_supabase_jwt

router = APIRouter(prefix="/ws/rooms", tags=["Rooms-WS"])

ROOM_CONN = {}          # { room_code: { participant_id: websocket } }
ROOM_LISTENERS = {}     # { room_code: asyncio.Task }


@router.websocket("/{code}")
async def room_ws(
    websocket: WebSocket,
    code: str,
    participant_id: str | None = Query(None),
    role: str = Query("normal"),
    display_name: str | None = None,
    db: Session = Depends(get_db)
):
    # -------------------
    # 1. Extract token from subprotocol
    # -------------------
    subproto = websocket.headers.get("sec-websocket-protocol")

    if not subproto:
        return await websocket.close(code=4403, reason="Missing subprotocol")

    try:
        protocol, token = subproto.split(",", 1)
        token = token.strip()
    except:
        return await websocket.close(code=4403, reason="Invalid subprotocol format")

    if not token:
        return await websocket.close(code=4403, reason="Missing token")

    # -------------------
    # 2. Verify JWT
    # -------------------
    try:
        payload = verify_supabase_jwt(token)
    except:
        return await websocket.close(code=4403, reason="Invalid token")

    user_id = payload["sub"]

    # -------------------
    # 3. Validate parameters
    # -------------------
    if not participant_id:
        return await websocket.close(code=4401, reason="Missing participant_id")

    room_repo = RoomRepository(db)
    if not room_repo.get_room_by_code(code):
        return await websocket.close(code=4404, reason="Room not found")

    # -------------------
    # 4. Accept WS ONCE with subprotocol
    # -------------------
    await websocket.accept(subprotocol="jwt")

    # -------------------
    # 5. Save connection
    # -------------------
    ROOM_CONN.setdefault(code, {})[participant_id] = websocket

    print(f"[WS CONNECT] room={code}, user={user_id}, pid={participant_id}")

    # -------------------
    # 6. Broadcast join via Redis
    # -------------------
    await redis_client.publish(
        f"room:{code}",
        json.dumps({
            "type": "presence.join",
            "participant_id": participant_id,
            "user_id": user_id,
            "role": role,
            "display_name": display_name
        })
    )

    # -------------------
    # 7. Create a single Redis listener per room
    # -------------------
    if code not in ROOM_LISTENERS:
        print(f"START LISTENER for room {code}")

        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"room:{code}")

        async def listen_redis():
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                data = json.loads(message["data"])
                print("Redis message:", data)

                # Broadcast to all WS in room
                for _pid, ws in list(ROOM_CONN.get(code, {}).items()):
                    try:
                        await ws.send_text(json.dumps(data))
                    except:
                        pass

        ROOM_LISTENERS[code] = asyncio.create_task(listen_redis())

    # -------------------
    # 8. WS message loop
    # -------------------
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            msg["participant_id"] = participant_id
            msg["user_id"] = user_id

            await redis_client.publish(
                f"room:{code}",
                json.dumps(msg)
            )

    except WebSocketDisconnect:
        pass

    finally:
        # Broadcast leave
        await redis_client.publish(
            f"room:{code}",
            json.dumps({
                "type": "presence.leave",
                "participant_id": participant_id,
                "user_id": user_id
            })
        )

        ROOM_CONN.get(code, {}).pop(participant_id, None)
        print(f"[WS DISCONNECT] {participant_id}")

