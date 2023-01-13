import sys

from time import sleep

from broadcast_listen_thread import BroadcastListenThread
from broadcast_send_thread import BroadcastSendThread
from file_transfer_thread import FileTransferThread
from lock import lock


def main():
    syncing_path = sys.argv[1]

    broadcast_send_thread = BroadcastSendThread(syncing_path)
    broadcast_listen_thread = BroadcastListenThread(syncing_path)
    file_transfer_thread = FileTransferThread(syncing_path)

    broadcast_send_thread.start()
    broadcast_listen_thread.start()
    file_transfer_thread.start()

    # TODO usunac keyword global wszedzie
    # TODO naprawic lub usunac struct, pickle jest w porządku ? a moze wlasny format

    # TODO da sie to zrobic lepiej?
    while True:
        try:
            # could have used signal.pause() on linux, but it's not available on windows
            sleep(1)
        except KeyboardInterrupt:
            print('KeyboardInterrupt')
            if lock.locked():
                lock.release()

            broadcast_send_thread.stop()
            broadcast_listen_thread.stop()
            file_transfer_thread.stop()

            broadcast_send_thread.join()
            broadcast_listen_thread.join()
            file_transfer_thread.join()

            sys.exit(0)


main()
