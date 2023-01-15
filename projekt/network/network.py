from typing import Any, Tuple

from network.cipher import xor
from utils.consts import BUFF_SIZE, MAX_UDP_PACKET_SIZE


# TODO add cipher/decipher

def recv(conn) -> bytes:
    received = conn.recv(BUFF_SIZE)
    # TODO handle exceptions
    return xor(received)


def recvfrom(sock) -> Tuple[bytes, Any]:
    received, addr = sock.recvfrom(MAX_UDP_PACKET_SIZE)
    # TODO handle exceptions
    return xor(received), addr


def recvall(sock) -> bytes:
    data = bytearray()
    while True:
        part = sock.recv(BUFF_SIZE)
        # TODO handle exceptions
        if not len(part):
            break
        data.extend(part)
    return xor(data)


def sendto(sock, data: bytes, address):
    sock.sendto(xor(data), address)
    # TODO handle exceptions


def sendall(conn, data: bytes):
    conn.sendall(xor(data))
    # TODO handle exceptions
