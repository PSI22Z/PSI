import signal
import sys

from dotenv import load_dotenv
from time import sleep

from file_system.fs import FileSystem
from threads.file_sync_client_thread import FileSyncClientThread
from threads.file_sync_server_thread import FileSyncServerThread
from threads.file_system_watcher_thread import FileSystemWatcherThread
from threads.file_server_thread import FileServerThread
from threads.file_sync_lock import file_sync_lock
from utils.logger import get_logger

threads = []
logger = get_logger("FileSync")


def stop():
    file_sync_lock.release()

    for t in threads:
        t.stop()
    for t in threads:
        t.join()

    logger.info('FileSync stopped')
    sys.exit(0)


def signal_handler(sig, frame):
    stop()


def main():
    if len(sys.argv) != 3:
        print("Usage: python main.py <path> <network_interface>")
        return

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    load_dotenv()

    syncing_path = sys.argv[1]
    network_interface = sys.argv[2]

    fs = FileSystem(syncing_path)

    logger.info('Starting FileSync')

    file_system_watcher_thread = FileSystemWatcherThread(fs)
    broadcast_send_thread = FileSyncServerThread(fs, network_interface)
    file_sync_client_thread = FileSyncClientThread(fs, network_interface)
    file_server_thread = FileServerThread(fs)

    global threads
    threads = [file_system_watcher_thread, broadcast_send_thread, file_sync_client_thread, file_server_thread]

    for t in threads:
        t.start()

    while True:
        try:
            # could have used signal.pause() on linux, but it's not available on windows
            sleep(1)
        except KeyboardInterrupt:
            stop()


main()
