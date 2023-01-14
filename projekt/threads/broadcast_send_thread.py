import os
import pickle
import socket
import struct
from datetime import datetime
from time import sleep

from utils.consts import UDP_PORT
from deleted_files import deleted_files
from lock import lock
from stoppable_thread import StoppableThread
from utils.utils import get_files_in_dir


class BroadcastSendThread(StoppableThread):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.previous_local_files_snapshot = []

    # uruchamiana cyklicznie (np. co 1 s) żeby wykrywać usunięte pliki
    # musi być często odpalana, żeby nie było sytuacji, że plik zostanie usunięty
    # a przyjdzie wiadomość od innego klienta, że taki plik istnieje
    def update_deleted_files(self):
        local_files = get_files_in_dir(self.path)

        for previous_file in self.previous_local_files_snapshot:
            if previous_file not in local_files:
                previous_file.is_deleted = True
                previous_file.modified_at = datetime.now()
                print(f"FILE {previous_file.filename} IS MARKED AS DELETED")
                deleted_files.add(previous_file)

        # trzeba tez kasowac z deleted_files jak sie pojawi
        for deleted_file in deleted_files.copy():
            if deleted_file in local_files:
                print(f"FILE {deleted_file.filename} IS NO LONGER DELETED")
                deleted_files.remove(deleted_file)

        self.previous_local_files_snapshot = local_files

    # używane do serializacji z użyciem struct (nie używane, bo problem z alignmentem)
    def prepare_struct(self, files):
        structs = []
        for file in files:
            filename = bytes(file.filename, "utf-8")
            structs.append(struct.pack('!100sddi?',
                                       filename,
                                       file.created_at.timestamp(),
                                       file.modified_at.timestamp(),
                                       file.size,
                                       file.is_deleted)
                           )
        return structs

    def run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1)

        broadcast_address = os.getenv("BROADCAST")
        if broadcast_address is None:
            broadcast_address = "192.168.0.255"

        while True and not self.stopped():
            lock.acquire()
            try:
                files = get_files_in_dir(self.path) + deleted_files.to_list()
                # structs = self.prepare_struct(files)
                msg = pickle.dumps(files)
                # msg = b";".join(structs)  # TODO
                print(f'broadcasting {list(map(lambda f: f"{f.filename} {f.is_deleted}", files))}')
                # TODO to nie zadziala jak mamy bardoz duzo plikow, trzeba dzielic wiadomosci?
                print(len(msg))
                sock.sendto(msg, (broadcast_address, UDP_PORT))
            finally:
                lock.release()
            for _ in range(15):
                self.update_deleted_files()
                sleep(1)

        print('BroadcastSendThread stopped')
        sock.close()
