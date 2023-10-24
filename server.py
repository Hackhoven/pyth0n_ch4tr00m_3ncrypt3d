import asyncio
import sys
from generator import generate_secure_user_id, generate_secure_chat_id
from server_db import clients_db, chatrooms_db

users_data = clients_db
chatrooms_data = chatrooms_db

async def send_message(writer, message):
    # Sends a message to a client
    writer.write(message.encode())
    await writer.drain()

header = 4096

class ChatClient:
    def __init__(self, writer="", reader=""):
        # Initialize a ChatClient
        self.id = ""
        self.writer = writer
        self.reader = reader
        self.name = ""
        self.chatroom_id = ""
        self.publicKey = ""
        self.client_address = writer.get_extra_info('peername') if writer is not None else None
        if self.client_address:
            print(f"Connection from {self.client_address} established")

    def get_user_profile(self):
        # Returns a dictionary representing the user's profile
        profile = {'name': self.name, 'chatroom_id': self.chatroom_id, 'writer': self.writer, 'publicKey': self.publicKey}
        return profile

    async def broadcast_to_all(self, message):
        # Broadcast a message to all connected clients
        for user_id, values in users_data.items():
            if user_id != self.id:
                await send_message(values['writer'], f"{message}")

    async def multicast_to_chat(self, message):
        # Multicast a message to clients in the same chatroom
        for user_id, values in users_data.items():
            if user_id != self.id and values['chatroom_id'] == self.chatroom_id:
                await send_message(values['writer'], f"{message}")

    async def send_message(self, message):
        # Send a message to this client
        message_bytes = message.encode()
        self.writer.write(message_bytes)
        await self.writer.drain()

    async def receive_message(self):
        # Receive a message from this client
        data = await self.reader.read(header)
        decoded_data = data.decode().strip()
        return decoded_data

    async def client_req_and_res(self, message):
        # Send a request to the client and await a response
        await self.send_message(message)
        return await self.receive_message()

    async def remove_client(self):
        # Remove a client from the server
        del users_data[self.name]
        await self.multicast_to_chat(f"{self.name} has left the chat!\n")
        self.writer.close()
        await self.writer.wait_closed()
        print(f"Connection is ceased for {self.client_address}")

    async def choose_name(self):
        # Allow the client to choose a name
        self.name = await self.client_req_and_res("Kh4k3nd1 ch4tr00m!\n Your username: \n")
        print(f"{self.name} joins the server")

        for user_id, values in users_data.items():
            if values['name'] == self.name:
                self.id = user_id
        if not self.id:
            self.id = generate_secure_user_id()

    async def choose_chat(self):
        option = None
        while option not in [1, 2]:
            chatroom_names = "\n".join(chatrooms_data.values())
            option = await self.client_req_and_res(f"\nYou can either create a room by typing 1,\n Or join an existing room by typing 2\n {chatroom_names}\n")
            try:
                option = int(option)
            except ValueError:
                option = None
            print(f"{option} is chosen")

        while True:
            if option == 1:
                chatroom_name = await self.client_req_and_res("Name of the chatroom: ")
                print(f"{chatroom_name} chatroom is created")
                self.chatroom_id = generate_secure_chat_id()
                chatrooms_data[self.chatroom_id] = chatroom_name
                break
            elif option == 2:
                chatroom_name = await self.client_req_and_res("Name of a chatroom: ")
                self.chatroom_id = find_id_by_name(chatroom_name, chatrooms_data)
                if not self.chatroom_id:
                    continue
                break
        await self.multicast_to_chat(f"\n{self.name} joins the chat\n")
        print(f"Hooray! {self.chatroom_id} chatroom is in the server")

    async def chat_with_others_in_room(self):
        while True:
            message = await self.receive_message()
            if "e2em|||" in message:
                _, client_id, encrypted_message = message.split("|||")
                await send_message(users_data[client_id]["writer"], f"{self.name}{message}")

    async def get_publicKey(self):
        self.publicKey = await self.receive_message()

    async def send_publicKeys_of_chatroom(self):
        for user_id, values in users_data.items():
            if values['chatroom_id'] == self.chatroom_id and user_id != self.id:
                await self.send_message(f"e2ek|||{user_id}|||{values['publicKey']}")

async def handle_client(reader, writer):
    client = ChatClient(writer, reader)
    await client.get_publicKey()
    print(f"{client.publicKey}")
    await client.choose_name()
    await client.choose_chat()
    users_data[client.id] = client.get_user_profile()
    await client.send_message(f"Enjoy our server Kh4nk3nd1 !\n")
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
        print("Proper command should be: python3 <fileName>.py <ip_address> <port>")
        sys.exit(1)

    ip = sys.argv[1]
    port = int(sys.argv[2])

    print(f"Server is started on {ip}:{port}")
    try:
        server = await asyncio.start_server(handle_client, ip, port)
        async with server:
            await server.serve_forever()

    finally:
        users_cut = {}
        for cid, values in users_data.items():
            users_cut[cid] = {'name': values['name'], 'chatroom_id': values['chatroom_id'], 'publicKey': values['publicKey']}
        server_db = open("server_db.py", "w")
        server_db.write(f"clients_db = {users_cut}\nchatrooms_db = {chatrooms_data}")
        server_db.close()

if __name__ == "__main__":
    asyncio.run(main())
