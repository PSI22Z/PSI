import os

from threads.stoppable_thread import StoppableThread
from utils.logger import get_logger
from utils.utils import safe_sleep


class FileSystemWatcherThread(StoppableThread):
    def __init__(self, fs):
        super().__init__()
        self.fs = fs
        self.fs_check_interval = int(os.getenv('FILE_SYSTEM_CHECK_INTERVAL'))
        self.logger = get_logger("FileSystemWatcher")

    def run(self) -> None:
        while True and not self.stopped():
            self.fs.update_local_and_deleted_files()
            safe_sleep(self.fs_check_interval, self.stopped)

        self.logger.debug('FileSystemWatcherThread stopped')
