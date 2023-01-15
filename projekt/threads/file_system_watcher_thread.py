import os

from threads.stoppable_thread import StoppableThread
from utils.utils import safe_sleep


class FileSystemWatcherThread(StoppableThread):
    def __init__(self, fs):
        super().__init__()
        self.fs = fs
        self.fs_check_interval = int(os.getenv('FILE_SYSTEM_CHECK_INTERVAL'))

    def run(self) -> None:
        while True and not self.stopped():
            # TODO trzeba ten lock?
            # file_sync_lock.acquire()  # wait for file sync to finish
            self.fs.update_local_and_deleted_files()
            # file_sync_lock.release()
            safe_sleep(self.fs_check_interval, self.stopped)

        print('FileSystemWatcherThread stopped')
