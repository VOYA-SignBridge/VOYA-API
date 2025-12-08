# app/routers/room_ws_router.py

import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json, asyncio
from app.core.redis_client import redis_client
from app.db.database import SessionLocal
from sqlalchemy.orm import Session
from app.repositories.room_repo import RoomRepository
from app.repositories.user_repo import UserRepository
from app.core.auth_middleware import verify_supabase_jwt
from app.services.sign_video_service import text_to_sign_videos
from app.services.room_service import RoomService
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
):
    # 1. Extract token from subprotocol
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

    # 2. Verify JWT
    try:
        payload = verify_supabase_jwt(token)
    except:
        return await websocket.close(code=4403, reason="Invalid token")

    supabase_id = payload["sub"]
    db= SessionLocal()
    try:
        user_repo= UserRepository(db)
        user= user_repo.get_by_supabase_id(supabase_id)
        if not user:
            user = user_repo.create_from_supabase(
                supabase_id=supabase_id,
                email=payload.get("email", ""),
                full_name=payload.get("email", "").split("@")[0]
            )
        internal_user_id= user.id
    finally:
        db.close()

    # 3. Validate parameters
    if not participant_id:
        return await websocket.close(code=4401, reason="Missing participant_id")

    db: Session = SessionLocal()
    try:
        room_repo = RoomRepository(db)
        if not room_repo.get_room_by_code(code):
            return await websocket.close(code=4404, reason="Room not found")
    finally:
        db.close()


    # 4. Accept WS ONCE with subprotocol
    await websocket.accept(subprotocol="jwt")
    
    # 5. Save connection
    ROOM_CONN.setdefault(code, {})[participant_id] = websocket

    print(f"[WS CONNECT] room={code}, user={internal_user_id}, pid={participant_id}")

    # 6. Broadcast join via Redis
    await redis_client.publish(
        f"room:{code}",
        json.dumps({
            "type": "presence.join",
            "participant_id": participant_id,
            "user_id": internal_user_id,
            "role": role,
            "display_name": display_name
        })
    )

    # 7. Create a single Redis listener per room
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
            if data["type"] == "room.ended":
                for pid, ws in list(ROOM_CONN.get(code, {}).items()):
                    try:
                        await ws.send_text(json.dumps({ "type": "room.ended" }))
                        await ws.close()
                    except:
                        pass

                ROOM_CONN.pop(code, None)
                return


        ROOM_LISTENERS[code] = asyncio.create_task(listen_redis())

    # 8. WS message loop
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            msg_type = msg.get("type")
            if msg_type == "chat.message":
                text = msg.get("text", "") or ""
                videos = text_to_sign_videos(text)

                response = {
                    "type" : "chat.message",
                    "room_code": code,
                    "text": text,
                    "videos": [v.dict() for v in videos],
                    "sender": 
                    {
                        "participant_id": participant_id,
                        "user_id": internal_user_id,
                        "role": role,
                        "display_name": display_name
                    },
                    "timestamp": int(time.time())

                }


            

                await redis_client.publish(
                    f"room:{code}",
                    json.dumps(response)
                )
            else:
                msg["participant_id"] = participant_id
                msg["user_id"] = internal_user_id
                msg["role"] = role

                await redis_client.publish(
                    f"room:{code}",
                    json.dumps(msg)
                )


    except WebSocketDisconnect:
        db = SessionLocal()
        try:
            room_service = RoomService(db)
            room_service.leave_room(code, internal_user_id, display_name)
        finally:
            db.close()
       

    finally:
        # Broadcast leave
        await redis_client.publish(
            f"room:{code}",
            json.dumps({
                "type": "presence.leave",
                "participant_id": participant_id,
                "user_id": internal_user_id
            })
        )

        ROOM_CONN.get(code, {}).pop(participant_id, None)
        if not ROOM_CONN.get(code):
             listener_task = ROOM_LISTENERS.pop(code, None)
             if listener_task:
                 listener_task.cancel()
        print(f"[WS DISCONNECT] {participant_id}")

