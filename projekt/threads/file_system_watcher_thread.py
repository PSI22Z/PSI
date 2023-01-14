from time import sleep

from threads.stoppable_thread import StoppableThread


class FileSystemWatcherThread(StoppableThread):
    def __init__(self, fs):
        super().__init__()
        self.fs = fs

    def run(self) -> None:
        while True and not self.stopped():
            # TODO trzeba ten lock?
            # file_sync_lock.acquire()  # wait for file sync to finish
            self.fs.update_local_and_deleted_files()
            # file_sync_lock.release()
            sleep(1)

        print('FileSystemWatcherThread stopped')
