import sys

from time import sleep

from file_system.fs import FileSystem
from threads.file_sync_client_thread import FileSyncClientThread
from threads.file_sync_server_thread import FileSyncServerThread
from threads.file_system_watcher_thread import FileSystemWatcherThread
from threads.file_server_thread import FileServerThread
from threads.file_sync_lock import file_sync_lock


def main():
    if len(sys.argv) != 3:
        print("Usage: python main.py <path> <network_interface>")
        return

    syncing_path = sys.argv[1]
    network_interface = sys.argv[2]

    fs = FileSystem(syncing_path)

    file_system_watcher_thread = FileSystemWatcherThread(fs)
    broadcast_send_thread = FileSyncServerThread(fs, network_interface)
    file_sync_client_thread = FileSyncClientThread(fs, network_interface)
    file_server_thread = FileServerThread(fs)

    file_system_watcher_thread.start()
    broadcast_send_thread.start()
    file_sync_client_thread.start()
    file_server_thread.start()

    # TODO naprawic lub usunac struct, pickle jest w porządku ? a moze wlasny format
    # TODO dodac logging
    # TODO dodac libke dotenv?
    # TODO przeniesc komunikacje do network (?)
    # TODO dodac szyfrowanie

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
            file_sync_client_thread.stop()
            file_server_thread.stop()

            file_system_watcher_thread.join()
            broadcast_send_thread.join()
            file_sync_client_thread.join()
            file_server_thread.join()

            sys.exit(0)


main()
