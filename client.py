#MLPLUB001
#LUBASI MILUPI
#Client code for Network Assignment 1

import threading
import socket
import sys

class Client:
    def __init__(self, server_ip, server_port, udp_port_num):
        self.nickname = input("Choose a nickname: ")
        self.server_ip = server_ip
        self.server_port = server_port
        self.udp_port_num = udp_port_num

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.server_ip, self.server_port))

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.server_ip, int(self.udp_port_num)))

        self.receive_thread = threading.Thread(target=self.receive)
        self.receive_thread.start()

        self.udp_recv_thread = threading.Thread(target=self.udp_receive)
        self.udp_recv_thread.start()

        self.write_thread = threading.Thread(target=self.write)
        self.write_thread.start()

    def receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('ascii')
                if message == 'Nickname':
                    self.client.send(self.nickname.encode('ascii'))
                elif message == 'port': # incase port number is needed by the server
                    self.client.send(self.udp_port_num.encode('ascii'))
                else:
                    print(message)
            except:
                print("Goodbye!")
                self.client.close()
                break

    def udp_receive(self):
        while True:
            try:
                private_message, address = self.udp_socket.recvfrom(1024)
                print(private_message.decode('ascii'))
            except:
                self.udp_socket.close()
                break

    def write(self):
        while True:
            message = input("")
            if message == "/private": # Prompt for sending a private message
                recv_port = eval(input("Enter receiver port: "))
                recv_IP = self.server_ip
                message = input("Message: ")
                message = f'{self.nickname}'+': '+message # Nickname attached to message so as to let the receiver know who is sending the message
                self.udp_socket.sendto(message.encode("ascii"), (recv_IP, recv_port))
            elif message == "/quit":
                self.client.close()
                self.udp_socket.close()
                break
            else:
                self.client.send(message.encode('ascii')) # Other messages and prompts are sent to the server to be executed

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py <server_ip> <server_port>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    udp_port_num = 12345  # You may modify this if needed

    client = Client(server_ip, server_port, udp_port_num)
