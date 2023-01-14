import os
import socket

from utils.consts import BUFF_SIZE


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


def recvall(conn):
    data = bytearray()
    while True:
        part = conn.recv(BUFF_SIZE)
        if not len(part):
            break
        data.extend(part)
    return data


def get_broadcast_address():
    broadcast_address = os.getenv("BROADCAST")
    if broadcast_address is None:
        broadcast_address = "192.168.0.255"
    return broadcast_address
