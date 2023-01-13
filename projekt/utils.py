import os
import socket
from datetime import datetime

from consts import BUFF_SIZE
from file import File


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


# TOOD przeniesc to do jakiegos file system providera
def get_files_in_dir(path) -> list[File]:
    filenames = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    files = []
    for filename in filenames:
        stat = os.stat(os.path.join(path, filename))
        files.append(File(
            filename=filename,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            size=stat.st_size
        ))
    return files
