import os
import pickle
import socket
import struct
from datetime import datetime

from file_system.fs import get_files_in_dir, save_file
from utils.consts import TCP_PORT, UDP_PORT
from deleted_files import deleted_files
from file_system.file import File
from file_sync_lock import file_sync_lock
from stoppable_thread import StoppableThread
from utils.utils import recvall, get_ip_address


# TODO rename to SeverThread?
class BroadcastListenThread(StoppableThread):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.host_ip = get_ip_address()

    def download_file(self, ip: str, filename: str):
        # TODO odbieranie duzych plikow nie dziala! nie wiem czemu
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, TCP_PORT))
        sock.sendall(filename.encode('utf-8'))
        data = recvall(sock)
        sock.close()
        if data is None:
            return bytearray()
        return data

    def unpack_structs(self, data):
        # TODO tutaj cos nie dziala, jezeli sie alignment nie zgadza
        # TODO struct.error: unpack requires a buffer of x bytes
        if len(data) == 0:
            return []
        structs = data.split(b";")
        files = []
        for strct in structs:
            filename, created_at, modified_at, size, is_deleted = struct.unpack('!100sddi?', strct)
            files.append(File(filename.decode('utf-8').split('\0', 1)[0],
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
                if addr[0] != self.host_ip:
                    file_sync_lock.acquire()
                    files = pickle.loads(data)
                    # files = self.unpack_structs(data)  # TODO
                    print(f'received {list(map(lambda f: f"{f.filename} {f.is_deleted}", files))} from {addr}')

                    # TODO tutaj skonczylem
                    # trzeba porownac files z tym co mamy w folderze

                    local_files = get_files_in_dir(self.path)
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
                            save_file(self.path, file, downloaded_file_content)
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
                                save_file(self.path, file, downloaded_file_content)
                    file_sync_lock.release()
            except socket.timeout:
                continue

        print('BroadcastListenThread stopped')
        sock.close()
