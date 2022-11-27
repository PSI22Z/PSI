import socket

LOCAL_IP = '0.0.0.0'
PORT = 8888
BUFFER_SIZE = 1024

msgFromServer = 'Hello UDP Client'
bytesToSend = str.encode(msgFromServer)

UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

UDPServerSocket.bind((LOCAL_IP, PORT))

print('UDP server up and listening')

while(True):
    print('Waiting for data...');
    bytesAddressPair = UDPServerSocket.recvfrom(BUFFER_SIZE)
    message = bytesAddressPair[0]
    address = bytesAddressPair[1]
    clientMsg = f'Message from Client: {message}'
    clientIP = f'Client IP Address: {address}'
    print(clientMsg)
    print(clientIP)
    
    UDPServerSocket.sendto(bytesToSend, address)
