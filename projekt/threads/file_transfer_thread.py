import os
import socket

from utils.consts import TCP_PORT, BUFF_SIZE
from lock import lock
from stoppable_thread import StoppableThread


class FileTransferThread(StoppableThread):
    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", TCP_PORT))
        sock.listen(5)
        sock.settimeout(1)

        while True and not self.stopped():
            try:
                conn, addr = sock.accept()
                filename = conn.recv(BUFF_SIZE).decode('utf-8')
                # filename = recv_msg(conn).decode('utf-8')
                print(f'received download request for {filename}')

                lock.acquire()
                with open(os.path.join(self.path, filename), 'rb') as file:
                    conn.sendall(file.read())
                conn.close()
                lock.release()
            except socket.timeout:
                continue

        print('FileTransferThread stopped')
        sock.close()
