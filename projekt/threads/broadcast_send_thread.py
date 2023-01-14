import os
import pickle
import socket
import struct
from datetime import datetime
from time import sleep

from utils.consts import UDP_PORT
from deleted_files import deleted_files
from file_sync_lock import file_sync_lock
from stoppable_thread import StoppableThread
from file_system.fs import get_files_in_dir


def get_broadcast_address():
    broadcast_address = os.getenv("BROADCAST")
    if broadcast_address is None:
        broadcast_address = "192.168.0.255"
    return broadcast_address


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

    # uruchamiana cyklicznie (np. co 1 s) żeby wykrywać usunięte pliki
    # musi być często odpalana, żeby nie było sytuacji, że plik zostanie usunięty
    # a przyjdzie wiadomość od innego klienta, że taki plik istnieje
    def update_deleted_files(self):
        # save current snapshot as previous
        previous_local_files_snapshot = self.current_local_files_snapshot
        self.current_local_files_snapshot = get_files_in_dir(self.path)

        for previous_file in previous_local_files_snapshot:
            if previous_file not in self.current_local_files_snapshot:
                # file was deleted
                previous_file.is_deleted = True
                previous_file.modified_at = datetime.now()
                print(f"FILE {previous_file.filename} IS MARKED AS DELETED")
                deleted_files.add(previous_file)

        for deleted_file in deleted_files.copy():
            # if file was deleted and then created again, it's not deleted anymore
            if deleted_file in self.current_local_files_snapshot:
                print(f"FILE {deleted_file.filename} IS NO LONGER DELETED")
                deleted_files.remove(deleted_file)

    # używane do serializacji z użyciem struct (nie używane, bo problem z alignmentem)
    # def prepare_struct(self, files):
    #     structs = []
    #     for file in files:
    #         filename = bytes(file.filename, "utf-8")
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
            for _ in range(15):
                # TODO da sie to poprawic?
                self.update_deleted_files()
                sleep(1)

        print('BroadcastSendThread stopped')
        self.close_udp_client_socket()
