import socket

LOCAL_IP = '0.0.0.0'
PORT = 8888
BUFFER_SIZE = 1024

msgFromServer = 'Hello TCP Client'
bytesToSend = str.encode(msgFromServer)

TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
TCPServerSocket.bind((LOCAL_IP, PORT))
TCPServerSocket.listen(1)

print('TCP server up and listening')

while(True):
    print('Waiting for data...')
    conn, address = TCPServerSocket.accept()  # accept new connection
    print("Connection from: " + str(address))
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        data = conn.recv(1024).decode()
        if not data:
            # if data is not received break
            break
        print("from connected user: " + str(data))
        conn.send(bytesToSend)  # send data to the client

    conn.close()  # close the connection