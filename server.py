import sys
import threading
import socket
import argparse


class Server:

    def __init__(self, host, port) -> None:

        self.host = host
        self.port = port
        self.FORMAT = 'ascii'

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()

        self.clients = []      # active clients
        self.nicknames = []    # usernames of the active clients
        self.chatrooms = {}  # chatroom stores tcp addr and port and list of members

    # modified so broadcasted message dooes not show to the client that sent the message
    def broadcast(self, message, this_client):

        message = message.encode(self.FORMAT)
        for client in self.clients:
            if client != this_client:
                client.send(message)

    def handle(self, client):
        # get the nickname of the client
        nick = self.nicknames[self.clients.index(client)]

        while True:
            try:
                message = client.recv(1024)

                if message.decode(self.FORMAT) == "/members":
                    heading = "Active chat members are:\n"
                    names = ''

                    for i, nickname in enumerate(self.nicknames, start=1):
                        names += f"{i}.{nickname}: {self.clients[i-1].getpeername()}"

                    # Edit: removed from for loop. Only send message once
                    client.send(f"{heading} {names}".encode(self.FORMAT))


                #Added option to appear ananymous and to stop appearing anonymous. Modified by MLPLUB001
                elif message.decode('ascii').startswith("/hide"):
                    #Get the nickname of the client that sent the prompt
                    client.send('Nickname'.encode(self.FORMAT)) # Prompt client to send nickname
                    nickname_to_remove = client.recv(1024).decode(self.FORMAT)

                    self.nicknames.remove(nickname_to_remove)  # remove nickname from the list
                elif message.decode('ascii').startswith("/reveal"):
                    client.send('Nickname'.encode(self.FORMAT))  # Prompt client to send nickname
                    nickname_to_add = client.recv(1024).decode(self.FORMAT)

                    if nickname_to_add in self.nicknames:
                        continue  # nickname already there, no need to re-add it
                    else:
                        self.nicknames.append(nickname_to_add)

                # added the option for clients to broadcast messages to other clients through the server
                elif message.decode(self.FORMAT) == "/broadcast":
                    client.send("Enter your message: ".encode(self.FORMAT))
                    client_msg = client.recv(1024).decode(self.FORMAT)
                    broad_msg = f"{nick}: {client_msg}"

                    self.broadcast(broad_msg, client)
                    client.send("Message broadcasted!".encode(self.FORMAT))

                elif message.decode('ascii').startswith("/create_room"):  # create a new room
                    room_name = message.decode('ascii').split(" ")[1]
                    self.chatrooms[room_name] = [client]
                    client.send(
                        f'Room {room_name} created successfully!'.encode('ascii'))
                    print("Created new chat room ", room_name)

                elif message.decode('ascii').startswith("/join"):  # join chatroom
                    room_name = message.decode('ascii').split(" ")[1]
                    if room_name in self.chatrooms:
                        self.chatrooms[room_name].append(client)
                        client.send(
                            f'Joined room {room_name} successfully!'.encode('ascii'))
                        print(f"{client} joined room ", room_name)
                    else:
                        client.send(
                            f'Room {room_name} does not exist!'.encode('ascii'))

                # send message in chatroom
                elif message.decode('ascii').startswith("/room"):
                    parts = message.decode('ascii').split(" ")
                    room_name = parts[1]
                    broadcast_msg_parts = parts[2:]
                    broadcast_msg = " ".join(broadcast_msg_parts)

                    members = self.chatrooms[room_name]

                    for member in members:
                        member.send(broadcast_msg.encode('ascii'))
                    print("Message broadcasted to members of ", room_name)

                elif message.decode('ascii') == "/get_rooms":  # get a list of chatrooms
                    heading = "Rooms:\n"
                    rooms = ''
                    for room, _ in self.chatrooms.items():
                        rooms = rooms + room
                    room_list = heading + rooms

                    client.send(room_list.encode('ascii'))
                    print("Send a list of rooms to ", client)
                elif message.decode('ascii').startswith("/leave"):  # leave the chatroom
                    room_name = message.decode('ascii').split(" ")[1]
                    members = self.chatrooms[room_name]
                    if client in members:
                        self.chatrooms[room_name].remove(client)
                        client.send(
                            f'Left room {room_name}'.encode('ascii'))
                        print(f"{client} left room ", room_name)
                    else:
                        client.send(
                            f'You are not a member of room {room_name}'.encode('ascii'))

                    print("Member left room ", room_name)

                elif message.decode('ascii').startswith("/quit"):
                    index = self.clients.index(client)
                    self.clients.remove(client)
                    client.close()

                    nickname = self.nicknames[index]
                    self.broadcast(
                        f'{nickname} left the chat!'.encode('ascii'))  # ***
                    self.nicknames.remove(nickname)
                    break


                else:
                    # server just listens without doing anything (might be used later for reliability idk)
                    pass

            except:
                self.clients.remove(client)
                self.nicknames.remove(nick)
                client.close()

                print(f"Closed connection: {nick}")
                self.broadcast(f"{nick} is offline", client)
                break

    def receive(self):
        print("Server is on & listening...")

        while True:
            try:
                client, address = self.server.accept()  # accept clients

                # Prompt client to send nickname
                client.send('Nickname'.encode(self.FORMAT))
                # Receive nickname, then apppend this nickname and client to our lists
                nickname = client.recv(1024).decode(self.FORMAT)

                print(f'Connected with [{nickname}: {address}]')

                self.nicknames.append(nickname)
                self.clients.append(client)

                # Send the message to this particular client that the connection was successful
                client.send('Connected to the server'.encode(self.FORMAT))
                # broadcast to active members that said client is online
                self.broadcast(f"Server: {nickname} is online!", client)

                thread = threading.Thread(target=self.handle, args=(client,))
                thread.start()

            except OSError as e:
                print("Socket error occurred:", e)
                print("Attempting to recover...")
                server.close()

                # Re-initialize server socket
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.bind((self.host, self.port))
                server.listen()

                print("Server reinitialized.")

            except KeyboardInterrupt as e:
                print(e)
                server.close()
                break

            except Exception as e:
                # unrecoverable case
                server.close()
                print("Error: ", str(e))
                sys.exit()


if __name__ == "__main__":  # main method

    args = argparse.ArgumentParser(description="Server is on...")
    args.add_argument('host', nargs='?', type=str,
                      default='196.42.113.205', help='Server IP address')
    args.add_argument('port', nargs='?', type=int,
                      default=44444, help='Server port number')
    arguments = args.parse_args()

    # parse arguments to Server class
    server = Server(arguments.host, arguments.port)
    server.receive()  # calling the receive function
