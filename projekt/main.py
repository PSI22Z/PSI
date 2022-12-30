import datetime
import os
import pickle
import socket
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

deleted_files = []
previous_files_snapshot = []

syncing_lock = threading.Lock()


def recvall(conn):
    BUFF_SIZE = 1024
    data = b''
    while True:
        part = conn.recv(BUFF_SIZE)
        data += part
        if len(part) < BUFF_SIZE:
            # either 0 or end of data
            break
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

        # compare files with previous_files_snapshot and set is_deleted flag
        # TODO poprawic
        global previous_files_snapshot, deleted_files
        for previous_file in previous_files_snapshot:
            if previous_file not in files:
                previous_file.is_deleted = True
                previous_file.modified_at = datetime.now()
                deleted_files.append(previous_file)

        # trzeba tez kasowac z deleted_files jak sie pojawi
        for deleted_file in deleted_files:
            if deleted_file in files:
                deleted_files.remove(deleted_file)

        previous_files_snapshot = files
        return files + deleted_files

    def run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(5)

        broadcast_address = os.getenv("BROADCAST")
        if broadcast_address is None:
            broadcast_address = "192.168.0.255"

        while True and not self.stopped():
            syncing_lock.acquire()
            try:
                files = self.get_files_in_dir()
                msg = pickle.dumps(files)
                print(len(msg))
                print(f'broadcasting {files}')
                sock.sendto(msg, (broadcast_address, UDP_PORT))
            finally:
                syncing_lock.release()
            sleep(15)

        print('BroadcastSendThread stopped')
        sock.close()


class BroadcastListenThread(StoppableThread):
    def __init__(self, path):
        super().__init__()
        self.path = path

    def get_local_in_dir(self) -> list[File]:
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

        return files + deleted_files

    def download_file(self, ip: str, filename: str):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, TCP_PORT))
        sock.sendall(filename.encode('utf-8'))
        data = recvall(sock)
        sock.close()
        return data

    def save_file(self, file: File, content):
        path = os.path.join(self.path, file.filename)
        with open(path, 'wb') as f:
            f.write(content)
        os.utime(path, (file.modified_at.timestamp(), file.modified_at.timestamp()))

    def run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(5)
        sock.bind(("", UDP_PORT))

        while True and not self.stopped():
            syncing_lock.acquire()
            try:
                data, addr = sock.recvfrom(40000)  # TODO jaki jest limit? czy trzeba dzielic na mniejsze wiadomosci?
                # w teorii ogranicza nas MTU (1500 bajtow), oraz rozmiar pakietu UDP (65535 bajtow)

                # ignore own messages
                # TODO przeciez tak nie mozna, bo IP bedzie takie samo. To jak to zrobic?
                if addr[0] != IP:
                    files = pickle.loads(data)
                    print(f"received message: {files} from {addr}")

                    # TODO tutaj skonczylem
                    # trzeba porownac files z tym co mamy w folderze

                    local_files = self.get_local_in_dir()
                    for file in files:
                        if file not in local_files:
                            # TODO trzeba podmienic metadane (daty np.)
                            print(f'HAVE TO DOWNLOAD {file.filename}, BECAUSE NOT IN LOCAL')
                            downloaded_file_content = self.download_file(addr[0], file.filename)
                            self.save_file(file, downloaded_file_content)
                        else:
                            local_file = next((f for f in local_files if f.filename == file.filename), None)

                            if file.is_deleted:
                                if local_file is not None and local_file.modified_at < file.modified_at:
                                    print(f'HAVE TO DELETE {file.filename}, BECAUSE IT IS MARKED AS DELETED')
                                    os.remove(os.path.join(self.path, file.filename))
                                    deleted_files.append(file)
                                    continue

                            if local_file is not None:
                                # TODO if local_file.modified_at < file.modified_at and local_file.size != file.size:
                                if local_file.modified_at < file.modified_at:
                                    # TODO trzeba sprawdzic skrot pliku?
                                    # TODO trzeba podmienic metadane (daty np.)
                                    print(f'HAVE TO DOWNLOAD {file.filename}, BECAUSE MODIFIED')
                                    downloaded_file_content = self.download_file(addr[0], file.filename)
                                    self.save_file(file, downloaded_file_content)
            except socket.timeout:
                continue
            finally:
                syncing_lock.release()

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
        sock.settimeout(5)

        while True and not self.stopped():
            syncing_lock.acquire()
            try:
                conn, addr = sock.accept()
                print(f'connection from {addr}')
                filename = recvall(conn).decode('utf-8')
                print(f'received {filename}')

                with open(os.path.join(self.path, filename), 'rb') as file:
                    file_content = file.read()
                    conn.sendall(file_content)

                conn.close()
            except socket.timeout:
                continue
            finally:
                syncing_lock.release()

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
            broadcast_send_thread.stop()
            broadcast_listen_thread.stop()
            file_transfer_thread.stop()

            broadcast_send_thread.join()
            broadcast_listen_thread.join()
            file_transfer_thread.join()
            sys.exit(0)


main()
