import socket
from time import sleep

from network.deser import serialize
from utils.consts import UDP_PORT
from threads.file_sync_lock import file_sync_lock
from threads.stoppable_thread import StoppableThread
from utils.utils import get_broadcast_address


class FileSyncServerThread(StoppableThread):
    def __init__(self, fs):
        super().__init__()
        self.sock = None
        self.fs = fs
        self.current_local_files_snapshot = []
        self.broadcast_address = get_broadcast_address()
        self.prepare_udp_server_socket()

    def prepare_udp_server_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.settimeout(1)

    def broadcast(self, msg):
        self.sock.sendto(msg, (self.broadcast_address, UDP_PORT))

    def close_udp_server_socket(self):
        self.sock.close()

    def run(self) -> None:
        while True and not self.stopped():
            file_sync_lock.acquire()  # wait for file sync to finish
            try:
                files = self.fs.local_files + self.fs.deleted_files.to_list()
                msg = serialize(files)
                print(f'broadcasting {list(map(lambda f: f"{f.filename} {f.is_deleted}", files))}')  # TODO logging
                self.broadcast(msg)
            finally:
                file_sync_lock.release()
            sleep(15)  # TODO konfigurowalny czas?

        print('FileSyncServerThread stopped')
        self.close_udp_server_socket()
