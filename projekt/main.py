import sys

from time import sleep

from threads.broadcast_listen_thread import BroadcastListenThread
from threads.broadcast_send_thread import BroadcastSendThread
from threads.file_transfer_thread import FileTransferThread
from threads.file_sync_lock import file_sync_lock


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <path>")
        return

    syncing_path = sys.argv[1]

    broadcast_send_thread = BroadcastSendThread(syncing_path)
    broadcast_listen_thread = BroadcastListenThread(syncing_path)
    file_transfer_thread = FileTransferThread(syncing_path)

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

            broadcast_send_thread.stop()
            broadcast_listen_thread.stop()
            file_transfer_thread.stop()

            broadcast_send_thread.join()
            broadcast_listen_thread.join()
            file_transfer_thread.join()

            sys.exit(0)


main()
