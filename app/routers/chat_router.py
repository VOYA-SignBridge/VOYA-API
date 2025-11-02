from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
from app.db.database import get_db
from app.repositories.message_repo import MessageRepository
from app.core.redis_client import redis_client
from app.services.call_service import CallService
from app.services.ai.ai_sign2text_service import predict_sign2text
router = APIRouter(prefix="/ws", tags=["Chat"])

chat_connection = {}
call_connection = {}
call_service = CallService()

@router.websocket("/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db= Depends(get_db)):
    await websocket.accept()
    chat_connection[user_id] = websocket

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"chat:{user_id}")

    message_repo = MessageRepository(db)

    try: 
        while True:
            message = await websocket.receive_text()
            if not message.strip():  
                continue
            data = json.loads(message)
            receiver_id = data["receiver_id"]
            content = data["content"]

            #Store message in DB
            message_repo.create_message(user_id, receiver_id, content)
            

            #Send to Redis Pub/Sub
            await redis_client.publish(f"chat:{receiver_id}", json.dumps({
                "sender_id": user_id,
                "content": content
            }))

    except WebSocketDisconnect:
        del chat_connection[user_id]
        await pubsub.unsubscribe(f"chat:{user_id}")
        await pubsub.close()




@router.websocket("/call/{user_id}")
async def call_websocket_endpoint(websocket: WebSocket, user_id: int):
    await call_service.connect_user(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            await call_service.handle_message(user_id, msg)
    except WebSocketDisconnect:
        await call_service.disconnect_user(user_id)


@router.websocket("/sign2text/{user_id}")
async def sign2text_websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    print(f"[sign2text] Connected user {user_id}")

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            keypoints = data.get("frames", [])
            target_id = data.get("target_id")

            result = predict_sign2text(keypoints)
            print(f"[sign2text] Prediction result for user {user_id}: {result}")

            if "error" in result:
                await websocket.send_text(json.dumps({
                    "type": "sign2text_error",
                    "error": result["error"]
                }))
                continue

            label = result.get("label", "")
            confidence = result.get("confidence", 0.0)
            print(f"[sign2text] Sending result: {label} (confidence: {confidence})")

            # Gửi về chính người khiếm thính
            await websocket.send_text(json.dumps({
                "type": "sign2text_result",
                "from": user_id,
                "to": target_id,
                "content": label,
                "confidence": confidence
            }))

            # Relay sang người đối diện trong call_service
            connections = call_service.connections  # ✅ dùng đúng nơi lưu
            print(f"[sign2text] Current connections: {list(connections.keys())}")

            # 🔁 Chỉ gửi kết quả cho đối phương (không echo lại)
            target_ws = call_service.connections.get(int(target_id))
            if target_ws:
                await target_ws.send_text(json.dumps({
                    "type": "sign2text_result",
                    "from": user_id,
                    "content": label,
                    "confidence": confidence
                }))
                print(f"[sign2text] ✅ Relayed result to user {target_id}")
            else:
                print(f"[sign2text] ⚠️ Target user {target_id} not connected")


    except Exception as e:
        print(f"[sign2text] Error for user {user_id}: {e}")
    finally:
        print(f"[sign2text] Disconnected user {user_id}")
