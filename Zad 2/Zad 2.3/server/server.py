import socket
import time

LOCAL_IP = '0.0.0.0'
PORT = 8888
BUFFER_SIZE = 1024

TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
TCPServerSocket.bind((LOCAL_IP, PORT))
TCPServerSocket.listen(5)

# set timeout for socket to 10 seconds
TCPServerSocket.settimeout(10)

print('TCP server up and listening')

while (True):
    print('Waiting for data...')
    try:
        conn, address = TCPServerSocket.accept()  # accept new connection
    except TimeoutError as e:
        print('No connection for 10 seconds, ex:', e)
        continue
    print("Connection from: " + str(address))
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        data = conn.recv(1024).decode()
        if not data:
            # if data is not received break
            break
        print("from connected user: " + str(data))

    conn.close()  # close the connection
