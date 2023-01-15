from utils.consts import BUFF_SIZE, MAX_UDP_PACKET_SIZE


# TODO add cipher/decipher

def recv(conn):
    return conn.recv(BUFF_SIZE)


def recvfrom(sock):
    return sock.recvfrom(MAX_UDP_PACKET_SIZE)


def recvall(sock):
    data = bytearray()
    while True:
        part = sock.recv(BUFF_SIZE)
        if not len(part):
            break
        data.extend(part)
    return data


def sendto(sock, data, address):
    sock.sendto(data, address)


def sendall(conn, data):
    conn.sendall(data)
