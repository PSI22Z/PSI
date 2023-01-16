import os
import socket

from network.deser import serialize
from network.network import sendto
from threads.file_sync_lock import file_sync_lock
from threads.stoppable_thread import StoppableThread
from utils.logger import get_logger
from utils.utils import get_broadcast_address, safe_sleep, get_files_stats


class FileSyncServerThread(StoppableThread):
    def __init__(self, fs, network_interface):
        super().__init__()
        self.sock = None
        self.port = int(os.getenv('PORT'))
        self.fs = fs
        self.current_local_files_snapshot = []
        self.broadcast_address = get_broadcast_address(network_interface)
        self.prepare_udp_server_socket()
        self.broadcast_interval = int(os.getenv('BROADCAST_INTERVAL'))
        self.logger = get_logger("FileSyncServer")

    def prepare_udp_server_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.settimeout(1)

    def broadcast(self, msg):
        try:
            sendto(self.sock, msg, (self.broadcast_address, self.port))
        except Exception as e:
            self.logger.error(f"Broadcasting failed: {e}, message length: {len(msg)}")

    def close_udp_server_socket(self):
        self.sock.close()

    def run(self) -> None:
        while True and not self.stopped():
            file_sync_lock.acquire()  # wait for file sync to finish
            try:
                files = self.fs.local_files + self.fs.deleted_files.to_list()
                msg = serialize(files)
                files_stats = get_files_stats(files)
                self.logger.debug(f"Broadcasting {files_stats[0]} local files and {files_stats[1]} deleted files")
                self.broadcast(msg)
            finally:
                file_sync_lock.release()
            safe_sleep(self.broadcast_interval, self.stopped)

        self.close_udp_server_socket()
        self.logger.debug('FileSyncServerThread stopped')
