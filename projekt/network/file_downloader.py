import socket

from utils.consts import ENCODING, TCP_PORT
from utils.utils import recvall


def download_file(ip: str, filename: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, TCP_PORT))
    sock.sendall(filename.encode(ENCODING))
    data = recvall(sock)
    sock.close()
    if data is None:
        return bytearray()
    return data
