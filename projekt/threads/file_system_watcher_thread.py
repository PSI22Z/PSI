from datetime import datetime
from time import sleep

from file_system.deleted_files import deleted_files
from file_system.fs import get_files_in_dir
from threads.file_sync_lock import file_sync_lock
from threads.stoppable_thread import StoppableThread


# TODO dodac nasluchiwanie na zmiany w folderze?

class FileSystemWatcherThread(StoppableThread):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.current_local_files_snapshot = []

    # uruchamiana cyklicznie (np. co 1 s) żeby wykrywać usunięte pliki
    # musi być często odpalana, żeby nie było sytuacji, że plik zostanie usunięty
    # a przyjdzie wiadomość od innego klienta, że taki plik istnieje
    def update_deleted_files(self):
        # save current snapshot as previous
        previous_local_files_snapshot = self.current_local_files_snapshot
        self.current_local_files_snapshot = get_files_in_dir(self.path)

        for previous_file in previous_local_files_snapshot:
            if previous_file not in self.current_local_files_snapshot:
                # file was deleted
                previous_file.is_deleted = True
                previous_file.modified_at = datetime.now()
                print(f"FILE {previous_file.filename} IS MARKED AS DELETED")
                deleted_files.add(previous_file)

        for deleted_file in deleted_files.copy():
            # if file was deleted and then created again, it's not deleted anymore
            if deleted_file in self.current_local_files_snapshot:
                print(f"FILE {deleted_file.filename} IS NO LONGER DELETED")
                deleted_files.remove(deleted_file)

    def run(self) -> None:
        while True and not self.stopped():
            # TODO trzeba ten lock?
            # file_sync_lock.acquire()  # wait for file sync to finish
            print("FILE SYSTEM WATCHER: UPDATE DELETED FILES")
            self.update_deleted_files()
            # file_sync_lock.release()
            sleep(1)

    print('FileSystemWatcherThread stopped')
