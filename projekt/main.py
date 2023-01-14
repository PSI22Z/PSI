import sys

from time import sleep

from file_system.fs import FileSystem
from threads.broadcast_listen_thread import BroadcastListenThread
from threads.broadcast_send_thread import BroadcastSendThread
from threads.file_system_watcher_thread import FileSystemWatcherThread
from threads.file_transfer_thread import FileTransferThread
from threads.file_sync_lock import file_sync_lock


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <path>")
        return

    syncing_path = sys.argv[1]

    fs = FileSystem(syncing_path)

    file_system_watcher_thread = FileSystemWatcherThread(fs)
    broadcast_send_thread = BroadcastSendThread(fs)
    broadcast_listen_thread = BroadcastListenThread(fs)
    file_transfer_thread = FileTransferThread(fs)

    file_system_watcher_thread.start()
    broadcast_send_thread.start()
    broadcast_listen_thread.start()
    file_transfer_thread.start()

    # TODO usunac keyword global wszedzie
    # TODO naprawic lub usunac struct, pickle jest w porządku ? a moze wlasny format
    # TODO dodac logging
    # TODO wlasna de/ser zamiast pickle

    # TODO da sie to zrobic lepiej?
    while True:
        try:
            # could have used signal.pause() on linux, but it's not available on windows
            sleep(1)
        except KeyboardInterrupt:
            print('KeyboardInterrupt')
            file_sync_lock.release()

            file_system_watcher_thread.stop()
            broadcast_send_thread.stop()
            broadcast_listen_thread.stop()
            file_transfer_thread.stop()

            file_system_watcher_thread.join()
            broadcast_send_thread.join()
            broadcast_listen_thread.join()
            file_transfer_thread.join()

            sys.exit(0)


main()
