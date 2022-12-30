import datetime
import os
import pickle
import socket
import struct
import sys
import threading
from dataclasses import dataclass
from time import sleep
from datetime import datetime


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


IP = get_ip_address()  # TODO dynamicznie?
UDP_PORT = 5005
TCP_PORT = 5006

deleted_files = set()
previous_files_snapshot = []

syncing_lock = threading.Lock()

BUFF_SIZE = 1024


def recvall(conn):
    data = bytearray()
    while True:
        part = conn.recv(BUFF_SIZE)
        if not len(part):
            break
        data.extend(part)
    return data


@dataclass
class File:
    filename: str
    created_at: datetime
    modified_at: datetime
    size: int
    is_deleted: bool = False

    # tymczasowe rozwiazanie, zeby ulatwic sprawdzanie istnienia pliku w kolekcji
    def __eq__(self, other):
        return self.filename == other.filename

    def __hash__(self):
        return hash(self.filename)


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class BroadcastSendThread(StoppableThread):
    def __init__(self, path):
        super().__init__()
        self.path = path

    def get_files_in_dir(self) -> list[File]:
        filenames = [f for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path, f))]

        files = []
        for filename in filenames:
            stat = os.stat(os.path.join(self.path, filename))

            files.append(File(
                filename=filename,
                created_at=datetime.fromtimestamp(stat.st_ctime),
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                size=stat.st_size
            ))

        return files

    def update_deleted_files(self):
        local_files = self.get_files_in_dir()

        global previous_files_snapshot, deleted_files
        for previous_file in previous_files_snapshot:
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

        previous_files_snapshot = local_files

    def prepare_struct(self, files):
        structs = []
        for file in files:
            filename = bytes(file.filename, "utf-8")
            structs.append(struct.pack(f'!I{len(filename)}sddi?',
                                       len(filename),
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
            syncing_lock.acquire()
            try:
                files = self.get_files_in_dir() + list(deleted_files)
                structs = self.prepare_struct(files)
                # msg = pickle.dumps(files)
                msg = b";".join(structs)  # TODO
                print(f'broadcasting {list(map(lambda f: f"{f.filename} {f.is_deleted}", files))}')
                # TODO to nie zadziala jak mamy bardoz duzo plikow, trzeba dzielic wiadomosci?
                print(len(msg))
                sock.sendto(msg, (broadcast_address, UDP_PORT))
            finally:
                syncing_lock.release()
            for _ in range(15):
                self.update_deleted_files()
                sleep(1)

        print('BroadcastSendThread stopped')
        sock.close()


class BroadcastListenThread(StoppableThread):
    def __init__(self, path):
        super().__init__()
        self.path = path

    def get_files_in_dir(self) -> list[File]:
        filenames = [f for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path, f))]

        files = []
        for filename in filenames:
            stat = os.stat(os.path.join(self.path, filename))

            files.append(File(
                filename=filename,
                created_at=datetime.fromtimestamp(stat.st_ctime),
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                size=stat.st_size
            ))

        return files

    def download_file(self, ip: str, filename: str):
        # TODO odbieranie duzych plikow nie dziala! nie wiem czemu
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, TCP_PORT))
        # send_msg(sock, filename.encode('utf-8'))
        sock.sendall(filename.encode('utf-8'))
        data = recvall(sock)
        # data = recvall(sock)
        sock.close()
        if data is None:
            return bytearray()
        return data

    def save_file(self, file: File, content):
        path = os.path.join(self.path, file.filename)
        with open(path, 'wb') as f:
            f.write(content)
        os.utime(path, (file.modified_at.timestamp(), file.modified_at.timestamp()))

    def unpack_structs(self, data):
        if len(data) == 0:
            return []
        structs = data.split(b";")
        files = []
        for strct in structs:
            (i,), data = struct.unpack('!I', strct[:4]), strct[4:]
            filename, created_at, modified_at, size, is_deleted = struct.unpack(f'!{i}sddi?', data)
            files.append(File(filename.decode('utf-8'),
                              datetime.fromtimestamp(created_at),
                              datetime.fromtimestamp(modified_at),
                              size,
                              is_deleted))
        return files

    def run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1)
        sock.bind(("", UDP_PORT))

        while True and not self.stopped():

            try:
                data, addr = sock.recvfrom(65507)  # TODO jaki jest limit? czy trzeba dzielic na mniejsze wiadomosci?
                # w teorii ogranicza nas MTU (1500 bajtow), oraz rozmiar pakietu UDP (65535 bajtow)

                # ignore own messages
                # TODO przeciez tak nie mozna, bo IP bedzie takie samo. To jak to zrobic?
                if addr[0] != IP:
                    syncing_lock.acquire()
                    # files = pickle.loads(data)
                    files = self.unpack_structs(data)  # TODO
                    print(f'received {list(map(lambda f: f"{f.filename} {f.is_deleted}", files))} from {addr}')

                    # TODO tutaj skonczylem
                    # trzeba porownac files z tym co mamy w folderze

                    local_files = self.get_files_in_dir()
                    for file in files:
                        local_file = next((f for f in local_files if f.filename == file.filename), None)

                        if file.is_deleted:
                            # file is deleted, checking if we have to delete
                            deleted_files.add(file)
                            if local_file is not None and local_file.modified_at < file.modified_at:
                                # TODO to chyba nie dziala poprawnie
                                # if we have a file locally and it is older than the deleted file, we delete it
                                print(f'HAVE TO DELETE {file.filename}, BECAUSE IT IS MARKED AS DELETED')
                                os.remove(os.path.join(self.path, file.filename))
                            continue
                        elif not file.is_deleted and file in deleted_files:
                            # file is not deleted, but we have it marked as deleted
                            # we have to remove it from deleted_files if it is newer than the deleted file
                            deleted_file = next((f for f in deleted_files if f.filename == file.filename), None)
                            if deleted_file is not None and deleted_file.modified_at < file.modified_at:
                                print(f'HAVE TO REMOVE {file.filename} FROM DELETED FILES')
                                deleted_files.remove(file)
                            continue

                        if local_file is None:
                            # we don't have the file locally, we have to download it
                            # TODO trzeba podmienic metadane (daty np.)
                            print(f'HAVE TO DOWNLOAD {file.filename}, BECAUSE NOT IN LOCAL')
                            downloaded_file_content = self.download_file(addr[0], file.filename)
                            self.save_file(file, downloaded_file_content)
                        else:
                            # we have the file locally, we have to check if we have to update it
                            # TODO if local_file.modified_at < file.modified_at and local_file.size != file.size:
                            if local_file.modified_at < file.modified_at:
                                # if we have a file locally and it is older than the file from the broadcast, we update it
                                # TODO trzeba sprawdzic skrot pliku?
                                # TODO trzeba podmienic metadane (daty np.)
                                print(f'HAVE TO DOWNLOAD {file.filename}, BECAUSE MODIFIED')
                                print(local_file)
                                print(file)
                                downloaded_file_content = self.download_file(addr[0], file.filename)
                                self.save_file(file, downloaded_file_content)
                    syncing_lock.release()
            except socket.timeout:
                continue

        print('BroadcastListenThread stopped')
        sock.close()


class FileTransferThread(StoppableThread):
    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((IP, TCP_PORT))
        sock.listen(5)
        sock.settimeout(1)

        while True and not self.stopped():
            try:
                conn, addr = sock.accept()
                filename = conn.recv(BUFF_SIZE).decode('utf-8')
                # filename = recv_msg(conn).decode('utf-8')
                print(f'received download request for {filename}')

                syncing_lock.acquire()
                with open(os.path.join(self.path, filename), 'rb') as file:
                    conn.sendall(file.read())
                conn.close()
                syncing_lock.release()
            except socket.timeout:
                continue

        print('FileTransferThread stopped')
        sock.close()


def main():
    path = sys.argv[1]

    broadcast_send_thread = BroadcastSendThread(path)
    broadcast_listen_thread = BroadcastListenThread(path)
    file_transfer_thread = FileTransferThread(path)

    broadcast_send_thread.start()
    broadcast_listen_thread.start()
    file_transfer_thread.start()

    while True:
        try:
            # could have used signal.pause() on linux, but it's not available on windows
            sleep(1)
        except KeyboardInterrupt:
            print('KeyboardInterrupt')
            if syncing_lock.locked():
                syncing_lock.release()

            broadcast_send_thread.stop()
            broadcast_listen_thread.stop()
            file_transfer_thread.stop()

            broadcast_send_thread.join()
            broadcast_listen_thread.join()
            file_transfer_thread.join()
            sys.exit(0)


main()
