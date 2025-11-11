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

# @router.websocket("/chat/{user_id}")
# async def websocket_endpoint(websocket: WebSocket, user_id: int, db= Depends(get_db)):
#     await websocket.accept()
#     chat_connection[user_id] = websocket

#     pubsub = redis_client.pubsub()
#     await pubsub.subscribe(f"chat:{user_id}")

#     message_repo = MessageRepository(db)

#     try: 
#         while True:
#             message = await websocket.receive_text()
#             if not message.strip():  
#                 continue
#             data = json.loads(message)
#             receiver_id = data["receiver_id"]
#             content = data["content"]

#             #Store message in DB
#             message_repo.create_message(user_id, receiver_id, content)
            

#             #Send to Redis Pub/Sub
#             await redis_client.publish(f"chat:{receiver_id}", json.dumps({
#                 "sender_id": user_id,
#                 "content": content
#             }))

#     except WebSocketDisconnect:
#         del chat_connection[user_id]
#         await pubsub.unsubscribe(f"chat:{user_id}")
#         await pubsub.close()




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
    await call_service.handle_sign2text(user_id, websocket)
