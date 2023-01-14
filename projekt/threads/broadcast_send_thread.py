import os
import pickle
import socket
from time import sleep

from utils.consts import UDP_PORT
from file_system.deleted_files import deleted_files
from threads.file_sync_lock import file_sync_lock
from threads.stoppable_thread import StoppableThread
from file_system.fs import get_files_in_dir
from utils.utils import get_broadcast_address


# TODO rename to ClientThread?
class BroadcastSendThread(StoppableThread):
    def __init__(self, path):
        super().__init__()
        self.sock = None
        self.path = path
        self.current_local_files_snapshot = []
        self.broadcast_address = get_broadcast_address()
        self.prepare_udp_client_socket()

    def prepare_udp_client_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.settimeout(1)

    def broadcast(self, msg):
        self.sock.sendto(msg, (self.broadcast_address, UDP_PORT))

    def close_udp_client_socket(self):
        self.sock.close()

    # używane do serializacji z użyciem struct (nie używane, bo problem z alignmentem)
    # def prepare_struct(self, files):
    #     structs = []
    #     for file in files:
    #         filename = bytes(file.filename, ENCODING)
    #         structs.append(struct.pack('!100sddi?',
    #                                    filename,
    #                                    file.created_at.timestamp(),
    #                                    file.modified_at.timestamp(),
    #                                    file.size,
    #                                    file.is_deleted)
    #                        )
    #     return structs

    def run(self) -> None:
        while True and not self.stopped():
            file_sync_lock.acquire()  # wait for file sync to finish
            try:
                files = get_files_in_dir(self.path) + deleted_files.to_list()
                # structs = self.prepare_struct(files)
                msg = pickle.dumps(files)
                # msg = b";".join(structs)  # TODO
                print(f'broadcasting {list(map(lambda f: f"{f.filename} {f.is_deleted}", files))}')  # TODO logging
                # TODO to nie zadziala jak mamy bardoz duzo plikow, trzeba dzielic wiadomosci?
                self.broadcast(msg)
            finally:
                file_sync_lock.release()
            sleep(15)  # TODO konfigurowalny czas?

        print('BroadcastSendThread stopped')
        self.close_udp_client_socket()
