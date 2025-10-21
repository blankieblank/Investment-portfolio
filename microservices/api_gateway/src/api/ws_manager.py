from fastapi import WebSocket
import logging
from typing import Dict


class ConnectionManager:
    def __init__(self):
        # Словарь для хранения активных соединений: {user_id: WebSocket}
        self.active_connections: Dict[int, WebSocket] = {}
        logging.info("ConnectionManager initialized.")

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logging.info(f"User {user_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logging.info(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)
            logging.info(f"Sent message to user {user_id}: {message}")


manager = ConnectionManager()
