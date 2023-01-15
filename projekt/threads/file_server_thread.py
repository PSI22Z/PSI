import os
import socket

from utils.consts import BUFF_SIZE, ENCODING
from threads.file_sync_lock import file_sync_lock
from threads.stoppable_thread import StoppableThread
from utils.logger import get_logger


class FileServerThread(StoppableThread):
    def __init__(self, fs):
        super().__init__()
        self.sock = None
        self.port = int(os.getenv('PORT'))
        self.fs = fs
        self.prepare_tcp_server_socket()
        self.logger = get_logger("FileServer")

    def prepare_tcp_server_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", self.port))
        self.sock.listen(5)
        self.sock.settimeout(1)

    def accept_connection(self):
        conn, addr = self.sock.accept()
        return conn, addr

    def close_tcp_server_socket(self):
        self.sock.close()

    def run(self) -> None:
        while True and not self.stopped():
            try:
                conn, addr = self.accept_connection()

                received = conn.recv(BUFF_SIZE)
                if len(received) == 0:
                    continue
                filename = received.decode(ENCODING)
                self.logger.info(f"Received download request for {filename} from {addr}")

                file_sync_lock.acquire()

                file_content = self.fs.read_file(filename)
                if file_content is not None:
                    conn.sendall(file_content)
                conn.close()

                file_sync_lock.release()
            except socket.timeout:
                continue

        self.close_tcp_server_socket()
        self.logger.debug('FileServerThread stopped')
