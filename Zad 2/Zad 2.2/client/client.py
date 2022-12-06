import socket
import sys

try:
    ADDRESS = socket.gethostbyname(sys.argv[1])
except socket.gaierror:
    print(f'Server "{sys.argv[1]}" is not running')
    quit()

PORT = 8888
BUFFER_SIZE = 1024

msgFromClient = 'Hello TCP Server'
bytesToSend = [str.encode(msgFromClient) for i in range(3)]

client_socket = socket.socket()
client_socket.connect((ADDRESS, PORT))

for message in bytesToSend:
    client_socket.sendall(len(message).to_bytes(4, byteorder='big', signed=False))
    client_socket.sendall(message)
    data = client_socket.recv(BUFFER_SIZE).decode()
    print(f'Received from server: {data}')

client_socket.close()