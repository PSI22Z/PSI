import datetime
import os
import pickle
import socket
import sys
import threading
from dataclasses import dataclass
from time import sleep
from datetime import datetime

IP = "192.168.0.10"
PORT = 5005

deleted_files = []
previous_files_snapshot = []


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

        while True and not self.stopped():
            files = self.get_files_in_dir()
            msg = pickle.dumps(files)
            print(len(msg))
            print(f'broadcasting {files}')
            sock.sendto(msg, ("192.168.0.255", PORT))
            sleep(15)

        print('BroadcastSendThread stopped')
        sock.close()


class BroadcastListenThread(StoppableThread):
    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(5)
        sock.bind(("", PORT))

        while True and not self.stopped():
            try:
                data, addr = sock.recvfrom(40000)  # TODO jaki jest limit? czy trzeba dzielic na mniejsze wiadomosci?
                # w teorii ogranicza nas MTU (1500 bajtow), oraz rozmiar pakietu UDP (65535 bajtow)

                # ignore own messages
                if addr != IP:
                    files = pickle.loads(data)
                    print(f"received message: {files} from {addr}")
            except socket.timeout:
                print('socket timeout')
                continue

        print('BroadcastListenThread stopped')
        sock.close()


def main():
    path = sys.argv[1]

    broadcast_send_thread = BroadcastSendThread(path)
    broadcast_listen_thread = BroadcastListenThread(path)

    broadcast_send_thread.start()
    broadcast_listen_thread.start()

    while True:
        try:
            # could have used signal.pause() on linux, but it's not available on windows
            sleep(1)
        except KeyboardInterrupt:
            print('KeyboardInterrupt')
            broadcast_send_thread.stop()
            broadcast_listen_thread.stop()

            broadcast_send_thread.join()
            broadcast_listen_thread.join()
            sys.exit(0)


main()
