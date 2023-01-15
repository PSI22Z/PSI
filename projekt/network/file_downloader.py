import os
import socket

from utils.consts import ENCODING
from utils.utils import recvall


def download_file(ip: str, filename: str):
    port = int(os.getenv('PORT'))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    sock.sendall(filename.encode(ENCODING))
    data = recvall(sock)
    sock.close()
    if data is None:
        return bytearray()
    return data
