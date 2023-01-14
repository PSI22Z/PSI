from datetime import datetime
from time import sleep

from threads.stoppable_thread import StoppableThread


# TODO dodac nasluchiwanie na zmiany w folderze?

class FileSystemWatcherThread(StoppableThread):
    def __init__(self, fs):
        super().__init__()
        self.fs = fs
        self.current_local_files_snapshot = []  # TODO move to fs?

    # uruchamiana cyklicznie (np. co 1 s) żeby wykrywać usunięte pliki
    # musi być często odpalana, żeby nie było sytuacji, że plik zostanie usunięty
    # a przyjdzie wiadomość od innego klienta, że taki plik istnieje
    # TODO move to fs?
    def update_deleted_files(self):
        # save current snapshot as previous
        previous_local_files_snapshot = self.current_local_files_snapshot
        self.current_local_files_snapshot = self.fs.local_files

        for previous_file in previous_local_files_snapshot:
            if previous_file not in self.current_local_files_snapshot:
                # file was deleted
                previous_file.is_deleted = True
                previous_file.modified_at = datetime.now()
                print(f"FILE {previous_file.filename} IS MARKED AS DELETED")
                self.fs.deleted_files.add(previous_file)

        for deleted_file in self.fs.deleted_files.copy():
            # if file was deleted and then created again, it's not deleted anymore
            if deleted_file in self.current_local_files_snapshot:
                print(f"FILE {deleted_file.filename} IS NO LONGER DELETED")
                self.fs.deleted_files.remove(deleted_file)

    # TODO move to fs?
    def update_local_files(self):
        self.fs.local_files = self.fs.get_files_in_dir()

    def run(self) -> None:
        while True and not self.stopped():
            # TODO trzeba ten lock?
            # file_sync_lock.acquire()  # wait for file sync to finish
            self.update_local_files()
            self.update_deleted_files()
            # file_sync_lock.release()
            sleep(1)

        print('FileSystemWatcherThread stopped')
