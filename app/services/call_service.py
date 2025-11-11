import json
from app.repositories.call_repo import CallRepository
from app.core.redis_client import redis_client
import asyncio
from app.services.ai.ai_sign2text_service import predict_sign2text
class CallService:
    def __init__(self):
        self.connections = {}

    async def connect_user(self, user_id: int, websocket):
        await websocket.accept()
        self.connections[user_id] = websocket
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"call:{user_id}")

        asyncio.create_task(self.listen_redis_message(user_id,pubsub))
        print(f"User {user_id} connected")

        # Notify other users that this user is ready for calls
        for uid, ws in self.connections.items():
            try:
                if uid != user_id:
                    await ws.send_text(json.dumps({
                        "type": "call_ready",
                        "user_id": user_id
                    }))
                    await websocket.send_text(json.dumps({
                        "type": "call_ready_ack",
                        "from": uid
                    }))
            except Exception as e:
                print(f"Error notifying user {uid} about user {user_id}: {e}")
                raise
    async def listen_redis_message(self, user_id: int, pubsub):
        ## Listen to Redis Pub/Sub messages and forward to websocket
        async for message in pubsub.listen():
            try:
                if message["type"]== "message":
                    data = json.loads(message["data"])
                    ws = self.connections.get(user_id)
                    if ws:
                        await ws.send_text(json.dumps(data))
            except Exception as e:
                print(f"[RedisListener] Error for user {user_id}: {e}")

    async def disconnect_user(self, user_id: int):
        try:
            print(f"User {user_id} disconnected")
            if user_id in self.connections:
                await self.connections[user_id].close()
                self.connections.pop(user_id)
            await redis_client.pubsub().unsubscribe(f"call:{user_id}")
        except Exception as e:
            print(f"Error disconnecting user {user_id}: {e}")
        

    async def handle_message(self, user_id: int, msg: dict):
        if not isinstance(msg, dict):
            print(f"[CallService] Invalid message format from {user_id}: {msg}")
            return
        target_id = msg.get("target_id") or msg.get("to")
        msg_type = msg.get("type")

        if not target_id or not msg_type:
            return
        
        target_id = int(target_id)
        print(f"[CallService] Handling message from {user_id} to {target_id}: {msg_type}")
        

       

        # --- Routing logic ---
        if msg_type == "call_request":
            await self.send_message(target_id, {
                "type": "call_ringing",
                "from": user_id
            })

        elif msg_type == "call_accept":
            await self.send_message(target_id, {
                "type": "call_accepted",
                "from": user_id
            })

        elif msg_type == "webrtc_signal":
            await self.send_message(target_id, {
                **msg,
                "from": user_id
            })

        elif msg_type == "call_end":
            await self.send_message(target_id, {
                "type": "call_ended",
                "from": user_id
            })
        elif msg_type == "sign2text_result":
            await self.send_message(target_id, {
                "type": "sign2text_result",
                "from": user_id,
                "content": msg.get("content", "")
            })

    async def handle_sign2text(self, user_id: int, websocket):
        """Connect websocket for sign2text handling"""
        await websocket.accept()
        print(f"[sign2text] Connected user {user_id}")

        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                keypoints = message.get("frames", [])
                target_id = message.get("target_id")

                # 🧠 Dự đoán sign2text
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

                #  Relay kết quả qua call_service (cho đối phương)
                target_ws = self.connections.get(int(target_id))
                if target_ws:
                    await target_ws.send_text(json.dumps({
                        "type": "sign2text_result",
                        "from": user_id,
                        "content": label,
                        "confidence": confidence
                    }))
                    print(f"[sign2text] ✅ Relayed result to user {target_id}")
                else:
                    # Nếu không cùng instance → gửi qua Redis
                    await redis_client.publish(f"call:{target_id}", json.dumps({
                        "type": "sign2text_result",
                        "from": user_id,
                        "content": label,
                        "confidence": confidence
                    }))
                    print(f"[sign2text] ⚠️ Target user {target_id} not connected (sent via Redis)")

        except Exception as e:
            print(f"[sign2text] Error for user {user_id}: {e}")
        finally:
            print(f"[sign2text] Disconnected user {user_id}")

    async def send_message(self, target_id: int, data: dict):
            if data.get("from") == target_id:
                return  # Không gửi cho chính mình
            target_ws = self.connections.get(target_id)
            #Receiver in same server instance
            if target_ws:
                await target_ws.send_text(json.dumps(data))
            #Receiver in different server instance
            else:
                await redis_client.publish(f"call:{target_id}", json.dumps(data))