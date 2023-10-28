import asyncio
import sys
from generator import *
from server_db import clients_db, chatrooms_db

# Initialize clients and chatrooms dictionaries
clients = clients_db
chatrooms = chatrooms_db
header = 4096

async def send_message(writer, message):
    writer.write(message.encode())
    await writer.drain()

class Client:
    def __init__(self, writer="", reader=""):
        # Initialize client attributes
        self.id = ""
        self.writer = writer
        self.reader = reader
        self.name = ""
        self.chatroom_id = ""
        self.publicKey = ""
        self.client_address = writer.get_extra_info('peername') if writer is not None else None
        if self.client_address:
            print(f"New connection from {self.client_address}")

    def get_user_profile(self):
        # Return client's profile as a dictionary
        profile = {
            'name': self.name,
            'chatroom_id': self.chatroom_id,
            'writer': self.writer,
            'publicKey': self.publicKey
        }
        return profile

    async def broadcast_to_all(self, message):
        # Broadcast a message to all connected clients except self
        for user_id, values in clients.items():
            if user_id != self.id:
                await send_message(values['writer'], f"{message}")

    async def multicast_to_chat(self, message):
        # Multicast a message to clients in the same chatroom except self
        for user_id, values in clients.items():
            if user_id != self.id and values['chatroom_id'] == self.chatroom_id:
                await send_message(values['writer'], f"{message}")

    async def send_message(self, message):
        # Send a message to the client
        message_bytes = message.encode()
        self.writer.write(message_bytes)
        await self.writer.drain()

    async def receive_message(self):
        # Receive a message from the client
        header = 4096
