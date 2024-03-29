import os
import socket

from network.deser import deserialize
from network.file_downloader import download_file
from network.network import recvfrom
from threads.file_sync_lock import file_sync_lock
from threads.stoppable_thread import StoppableThread
from utils.logger import get_logger
from utils.utils import get_ip_address, get_files_stats


class FileSyncClientThread(StoppableThread):
    def __init__(self, fs, network_interface):
        super().__init__()
        self.sock = None
        self.port = int(os.getenv('PORT'))
        self.fs = fs
        self.host_ip = get_ip_address(network_interface)
        self.prepare_udp_client_socket()
        self.logger = get_logger("FileSyncClient")

    def prepare_udp_client_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.settimeout(1)
        self.sock.bind(("", self.port))

    def receive(self):
        data, addr = recvfrom(self.sock)
        return data, addr

    def close_udp_client_socket(self):
        self.sock.close()

    def find_local_file(self, local_files, filename):
        return next((f for f in local_files if f.filename == filename), None)

    def handle_deleted_remote_file(self, remote_file, local_file):
        # file is deleted, checking if we have to delete
        self.fs.deleted_files.add(remote_file)
        if local_file is not None and local_file.modified_at < remote_file.modified_at:
            # if we have a file locally, and it is older than the deleted file, we delete it
            self.logger.info(f"Deleting local {remote_file.filename}, because it is marked as deleted")
            self.fs.delete_file(remote_file.filename)

    def handle_undeleted_remote_file(self, remote_file, server_ip):
        # file is not deleted, but we have it marked as deleted
        # we have to remove it from deleted_files if it is newer than the deleted file
        deleted_file = next((f for f in self.fs.deleted_files if f.filename == remote_file.filename), None)
        if deleted_file is not None and deleted_file.modified_at < remote_file.modified_at:
            self.logger.info(f"Removing {remote_file.filename} from deleted files. Downloading it from {server_ip}")
            self.fs.deleted_files.remove(remote_file)
            self.upsert_local_file(remote_file, server_ip)

    def handle_new_remote_file(self, remote_file, server_ip):
        # we don't have the file locally, we have to download it
        self.logger.info(f"Downloading {remote_file.filename} from {server_ip}, because it's not in local files")
        self.upsert_local_file(remote_file, server_ip)

    def handle_existing_remote_file(self, remote_file, local_file, server_ip):
        # we have the file locally, we have to check if we have to update it
        if local_file.modified_at < remote_file.modified_at:
            # if we have a file locally, and it is older than the file from the broadcast, we update it
            self.logger.info(f"Downloading {remote_file.filename} from {server_ip}, because it's modified")
            self.upsert_local_file(remote_file, server_ip)

    def upsert_local_file(self, remote_file, server_ip):
        downloaded_file_content = download_file(server_ip, remote_file.filename)
        self.fs.save_file(remote_file, downloaded_file_content)

    def handle_remote_files(self, data, server_ip):
        file_sync_lock.acquire()  # wait for file sync to finish

        remote_files = deserialize(data, self.logger)
        files_stats = get_files_stats(remote_files)
        self.logger.debug(f"Received {files_stats[0]} local files and {files_stats[1]} deleted files from {server_ip}")

        local_files = self.fs.local_files

        for remote_file in remote_files:
            local_file = self.find_local_file(local_files, remote_file.filename)

            if remote_file.is_deleted:
                self.handle_deleted_remote_file(remote_file, local_file)
                continue
            elif not remote_file.is_deleted and remote_file in self.fs.deleted_files:
                self.handle_undeleted_remote_file(remote_file, server_ip)
                continue

            if local_file is None:
                self.handle_new_remote_file(remote_file, server_ip)
            else:
                self.handle_existing_remote_file(remote_file, local_file, server_ip)

        file_sync_lock.release()

    def run(self) -> None:
        while True and not self.stopped():
            try:
                data, addr = self.receive()
                if data is None:
                    continue
                server_ip = addr[0]

                # ignore own messages
                if server_ip != self.host_ip:
                    self.handle_remote_files(data, server_ip)
            except socket.timeout:
                continue

        self.close_udp_client_socket()
        self.logger.debug('FileSyncClientThread stopped')
