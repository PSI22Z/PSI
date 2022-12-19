import socket
import sys
import time

try:
    ADDRESS = socket.gethostbyname(sys.argv[1])
except socket.gaierror:
    print(f'Server "{sys.argv[1]}" is not running')
    quit(1)

PORT = 8888
BUFFER_SIZE = 1024

msgFromClient = 'Hello TCP Server'
bytesToSend = [str.encode(msgFromClient) for i in range(3)]

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# set timeout for socket to 10 seconds
client_socket.settimeout(10)

try:
    client_socket.connect((ADDRESS, PORT))
except BaseException as e:
    print('No connection for 10 seconds, ex:', e)
    client_socket.close()
    quit(2)

for message in bytesToSend:
    print(f'Sending: {message}')
    client_socket.sendall(message)
    time.sleep(5)

client_socket.close()
