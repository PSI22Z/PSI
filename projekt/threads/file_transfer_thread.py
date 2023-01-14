import socket

from file_system.fs import read_file
from utils.consts import TCP_PORT, BUFF_SIZE
from threads.file_sync_lock import file_sync_lock
from threads.stoppable_thread import StoppableThread
from utils.utils import recvall


# TODO rename to FileSeverThread?


class FileTransferThread(StoppableThread):
    def __init__(self, path):
        super().__init__()
        self.sock = None
        self.path = path
        self.prepare_tcp_server_socket()

    def prepare_tcp_server_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", TCP_PORT))
        self.sock.listen(5)
        self.sock.settimeout(1)

    def accept_connection(self):
        conn, _ = self.sock.accept()
        return conn

    def close_tcp_server_socket(self):
        self.sock.close()

    def run(self) -> None:
        while True and not self.stopped():
            try:
                conn = self.accept_connection()

                filename = conn.recv(BUFF_SIZE).decode('utf-8')  # TODO mozna tu uzywac recvall?
                # filename = recvall(conn).decode('utf-8')
                print(f'received download request for {filename}')

                file_sync_lock.acquire()

                file_content = read_file(self.path, filename)
                conn.sendall(file_content)
                conn.close()

                file_sync_lock.release()
            except socket.timeout:
                continue

        print('FileTransferThread stopped')
        self.close_tcp_server_socket()
