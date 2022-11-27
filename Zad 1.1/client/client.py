import socket
import sys

try:
    ADDRESS = socket.gethostbyname(sys.argv[1])
except socket.gaierror:
    print(f'Server "{sys.argv[1]}" is not running')
    quit()

PORT = 8888
BUFFER_SIZE = 1024

msgFromClient = 'Hello UDP Server'
bytesToSend = [str.encode(msgFromClient + f' {i}') for i in range(3)]

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

for message in bytesToSend:
    UDPClientSocket.sendto(message, (ADDRESS, PORT))
    msgFromServer = UDPClientSocket.recvfrom(BUFFER_SIZE)
    print(f'Message from Server "{msgFromServer[0].decode("utf-8")}"')