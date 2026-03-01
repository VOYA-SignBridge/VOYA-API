# # app/services/room_ws_service.py

# import json
# import asyncio

# class RoomWSService:
#     def __init__(self, redis_client, room_repo):
#         self.redis = redis_client
#         self.room_repo = room_repo

#         # WS connections cache
#         self.ROOM_CONN = {}   # { room_code: { participant_id: ws } }

#     async def connect(self, websocket, code, participant_id, user_id, role, name):
#         self.ROOM_CONN.setdefault(code, {})[participant_id] = websocket

        
#         await self.redis.publish(
#             f"room:{code}",
#             json.dumps({
#                 "type": "presence.join",
#                 "participant_id": participant_id,
#                 "user_id": user_id,
#                 "role": role,
#                 "name": name
#             })
#         )

#     async def disconnect(self, code, participant_id, user_id):
#         await self.redis.publish(
#             f"room:{code}",
#             json.dumps({
#                 "type": "presence.leave",
#                 "participant_id": participant_id,
#                 "user_id": user_id,
#                 "no_echo": True
#             })
#         )

#         self.ROOM_CONN.get(code, {}).pop(participant_id, None)

#     async def broadcast_from_redis(self, code, pubsub, participant_id):
#         async for message in pubsub.listen():
#             if message["type"] != "message":
#                 continue

#             data = json.loads(message["data"])

#             if data.get("participant_id") == participant_id and data.get("no_echo"):
#                 continue

#             for pid, ws in list(self.ROOM_CONN.get(code, {}).items()):
#                 try:
#                     await ws.send_text(json.dumps(data))
#                 except:
#                     pass
