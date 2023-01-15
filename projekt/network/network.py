from typing import Any, Tuple

from network.cipher import xor
from utils.consts import BUFF_SIZE, MAX_UDP_PACKET_SIZE


def recv(sock) -> bytes | None:
    received = sock.recv(BUFF_SIZE)
    if not received:
        return None
    return xor(received)


def recvfrom(sock) -> Tuple[bytes, Any] | Tuple[None, None]:
    received, addr = sock.recvfrom(MAX_UDP_PACKET_SIZE)
    if not received:
        return None, None
    return xor(received), addr


def recvall(sock) -> bytes:
    data = bytearray()
    while True:
        part = sock.recv(BUFF_SIZE)
        if part is None or not len(part):
            break
        data.extend(part)
    return xor(data)


def sendto(sock, data: bytes, address):
    result = sock.sendto(xor(data), address)
    if result != len(data):
        raise Exception("Not all data was sent")


def sendall(sock, data: bytes):
    sock.sendall(xor(data))
