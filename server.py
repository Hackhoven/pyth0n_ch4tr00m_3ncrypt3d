import asyncio
import sys
from generator import *
from server_db import clients_db, chatrooms_db

clients = clients_db
chatrooms = chatrooms_db
header = 4096

async def send_message(writer, message):
    writer.write(message.encode())
    await writer.drain()

class Client:
    def __init__(self, writer="", reader=""):
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
        profile = {
            'name': self.name,
            'chatroom_id': self.chatroom_id,
            'writer': self.writer,
            'publicKey': self.publicKey
        }
        return profile

    async def broadcast_to_all(self, message):
        for user_id, values in clients.items():
            if user_id != self.id:
                await send_message(values['writer'],f"{message}")
    
    async def multicast_to_chat(self, message):        
        for user_id, values in clients.items():
            if user_id != self.id and values['chatroom_id'] == self.chatroom_id:
                await send_message(values['writer'],f"{message}")


    async def send_message(self, message):
        message_bytes = message.encode()
        self.writer.write(message_bytes)
        await self.writer.drain()

    async def receive_message(self):
        header = 4096
        data = await self.reader.read(header)
        decoded_data = data.decode().strip()
        return decoded_data

    async def client_req_and_res(self, message):
        await self.send_message(message)
        return await self.receive_message()

    async def remove_client(self):        
        del clients[self.name]
        await self.multicast_to_chat(f"{self.name} has left the chat!\n")
        self.writer.close()
        await self.writer.wait_closed()
        print(f"Connection closed for {self.client_address}")

    async def choose_name(self):
        self.name = await self.client_req_and_res("Welcome to the Kh4nk3nd1 ch4tr00m!\nYour username: \n")
        print(f"{self.name} is in the server")
        for user_id, values in clients.items():
            if values['name'] == self.name:
                self.id = user_id
        if not self.id: 
            self.id = generate_secure_user_id()

    async def choose_chat(self):
        option = ""
        while option not in [1, 2]:
            chatroom_names = "\n".join(chatrooms.values())
            option = await self.client_req_and_res(f"\nCreate a neww room by typing 1\nSelect a room by typing 2:\n{chatroom_names}\n")
            try:
                option = int(option)
            except ValueError:
                option = None
            print(f"{option} is selected")
        while True:
            if option == 1: 
                chatroom_name = await self.client_req_and_res("Enter the name of a new chatroom: ")
                print(f"{chatroom_name} chatroom is created")
                self.chatroom_id = generate_secure_chat_id() 
                chatrooms[self.chatroom_id] = chatroom_name
                break
            elif option == 2:
                chatroom_name = await self.client_req_and_res("Enter the name of a chatroom: ")
                self.chatroom_id = find_id_by_name(chatroom_name, chatrooms)
                if not self.chatroom_id: continue
                break
        await self.multicast_to_chat(f"\n{self.name} is in the chat!\n")
        print(f"{self.chatroom_id} chatroom is here in the server")

    async def chat_with_others_in_room(self):
        while True:
            message = await self.receive_message()
            if "e2em|||" in message:
                _, client_id, encrypted_message = message.split("|||")
                await send_message(clients[client_id]["writer"], f"{self.name}{message}")
    
    async def get_publicKey(self):
        self.publicKey = await self.receive_message()
    
    async def send_publicKeys_of_chatroom(self):
        for user_id, values in clients.items():
            if values['chatroom_id'] == self.chatroom_id and user_id != self.id:
                await self.send_message(f"e2ek|||{user_id}|||{values['publicKey']}")

async def handle_client(reader, writer):
    client = Client(writer, reader)
    await client.get_publicKey()
    print(f"{client.publicKey}")
    await client.choose_name()
    await client.choose_chat()
    clients[client.id] = client.get_user_profile()
    await client.send_message(f"Enjoy our server Kh4nk3nd1!\n")
    await client.multicast_to_chat(f"e2ek|||{client.id}|||{client.publicKey}")
    await client.send_publicKeys_of_chatroom()
    try:
        await client.chat_with_others_in_room()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error handling client {client.name}: {e}")
    finally:
        await client.remove_client()
        del client

async def main():
    if len(sys.argv) != 3:
        print("Command: python file.py <ip_address> <port>")
        sys.exit(1)

    ip = sys.argv[1]
    port = int(sys.argv[2])

    print(f"Server is started on {ip}:{port}")
    try:
        server = await asyncio.start_server(handle_client, ip, port)
        async with server:
            await server.serve_forever()
    finally:
        clients_cut = {}
        for cid, values in clients.items():
            clients_cut[cid] = {'name': values['name'], 'chatroom_id': values['chatroom_id'], 'publicKey': values['publicKey']}
        server_db = open("server_db.py", "w")
        server_db.write(f"clients_db = {clients_cut}\nchatrooms_db = {chatrooms}")
        server_db.close()

if __name__ == "__main__":
    asyncio.run(main())
