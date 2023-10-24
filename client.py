import socket
import threading
import rsa
import sys

class ChatClientSocket:

    def __init__(self, ip, port):
        # Initialize the ChatClientSocket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, port))
        self.public_key, self.private_key = rsa.newkeys(2048)
        self.other_clients_in_chat = {}

    def send(self):
        # Send messages to the server or other clients
        while True:
            message = input("> ")

            if message.lower() == 'exit':
                break

            if len(self.other_clients_in_chat) == 0:
                # No other clients in the chat, send a regular message to the server
                self.socket.send(message.encode())

            else:
                # Encrypt and send the message to each client
                for client_id, public_key in self.other_clients_in_chat.items():
                    encrypted_message = rsa.encrypt(message.encode(), public_key)
                    message_to_send = f"e2em|||{client_id}|||{encrypted_message}"
                    self.socket.send(message_to_send.encode())

    def receive(self):
        # Receive and process messages from the server or other clients
        while True:
            data = self.socket.recv(4096)
            message = data.decode().strip()

            if "e2em|||" in message:  # Decrypting messages
                name, client_id, encrypted_message = message.split("|||")
                decrypted_message = rsa.decrypt(eval(encrypted_message), self.private_key).decode()
                print(f"<message from {name[:-4]}> {decrypted_message}")

            elif "e2ek|||" in message:
                parts = message.split("e2ek|||")
                for part in parts[1:]:
                    client_id, public_key_encoded = part.split("|||")
                    self.other_clients_in_chat[client_id] = rsa.PublicKey.load_pkcs1(public_key_encoded)
            else:
                print(f"server: {message}")

def main():

    if len(sys.argv) != 3:
        print("Proper command should be: python3 <fileName>.py <ip_address> <port>")
        sys.exit(1)

    ip_address = sys.argv[1]
    port = int(sys.argv[2])

    my_socket = ChatClientSocket(ip_address, port)

    receiver = threading.Thread(target=my_socket.receive)
    my_socket.socket.send(my_socket.public_key.save_pkcs1())
    receiver.start()

    try:
        my_socket.send()

    except KeyboardInterrupt:
        print("Connection is ceased by the user.")

    finally:
        my_socket.socket.close()

if __name__ == "__main__":
    main()
