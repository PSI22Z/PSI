import socket

LOCAL_IP = '0.0.0.0'
PORT = 8888
BUFFER_SIZE = 2
INTEGER_SIZE = 4

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
        data_length = int.from_bytes(conn.recv(INTEGER_SIZE), byteorder='big', signed=False)
        if not data_length:
            break
        print(f'receiving message of length {data_length}: ')
        data = ''
        while data_length > 0:
            message_part = conn.recv(BUFFER_SIZE).decode()
            data += message_part
            data_length -= len(message_part)
            if not data:
                # if data is not received break
                break
        print("from connected user: " + str(data))
        conn.send(bytesToSend)  # send data to the client

    conn.close()  # close the connection