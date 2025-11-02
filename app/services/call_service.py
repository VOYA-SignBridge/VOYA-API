import json

class CallService:
    def __init__(self):
        self.connections = {}

    async def connect_user(self, user_id: int, websocket):
        await websocket.accept()
        self.connections[user_id] = websocket
        print(f"User {user_id} connected")

        # thông báo ready/ack
        for uid, ws in self.connections.items():
            if uid != user_id:
                await ws.send_text(json.dumps({
                    "type": "call_ready",
                    "user_id": user_id
                }))
                await websocket.send_text(json.dumps({
                    "type": "call_ready_ack",
                    "from": uid
                }))

    async def disconnect_user(self, user_id: int):
        print(f"User {user_id} disconnected")
        self.connections.pop(user_id, None)

    async def handle_message(self, user_id: int, msg: dict):
        target_id = msg.get("target_id") or msg.get("to")
        msg_type = msg.get("type")

        if not target_id or int(target_id) not in self.connections:
            ws = self.connections.get(user_id)
            if ws:
                await ws.send_text(json.dumps({
                    "type": "error",
                    "message": f"User {target_id} not connected"
                }))
            return

        target_ws = self.connections[int(target_id)]

        # --- Routing logic ---
        if msg_type == "call_request":
            await target_ws.send_text(json.dumps({
                "type": "call_ringing",
                "from": user_id
            }))

        elif msg_type == "call_accept":
            await target_ws.send_text(json.dumps({
                "type": "call_accepted",
                "from": user_id
            }))

        elif msg_type == "webrtc_signal":
            await target_ws.send_text(json.dumps({
                **msg,
                "from": user_id
            }))

        elif msg_type == "call_end":
            await target_ws.send_text(json.dumps({
                "type": "call_ended",
                "from": user_id
            }))
        elif msg_type == "sign2text_result":
            await target_ws.send_text(json.dumps({
                "type": "sign2text_result",
                "from": user_id,
                "content": msg.get("content")
            }))
