import os
from datetime import datetime

from file_system.deleted_files import DeletedFiles
from file_system.file import File


class FileSystem:
    def __init__(self, path):
        if not os.path.isdir(path):
            raise Exception('Not a directory')
        self.path = path
        self.local_files = self.__get_files_in_dir()
        self.deleted_files = DeletedFiles()

    def update_local_and_deleted_files(self):
        previous_local_files_snapshot = self.local_files
        self.__update_local_files()
        self.__update_deleted_files(previous_local_files_snapshot)

    def save_file(self, file: File, content):
        try:
            path = os.path.join(self.path, file.filename)
            with open(path, 'wb') as f:
                f.write(content)
            os.utime(path, (file.modified_at.timestamp(), file.modified_at.timestamp()))
        except Exception as e:
            print(e)  # TODO logging

    def read_file(self, filename: str) -> bytes | None:
        try:
            with open(os.path.join(self.path, filename), 'rb') as file:
                return file.read()
        except Exception as e:
            print(e)  # TODO logging
            return None

    def delete_file(self, filename: str):
        try:
            os.remove(os.path.join(self.path, filename))
        except Exception as e:
            print(e)  # TODO logging

    def __update_local_files(self):
        self.local_files = self.__get_files_in_dir()

    def __update_deleted_files(self, previous_local_files_snapshot):
        for previous_file in previous_local_files_snapshot:
            if previous_file not in self.local_files:
                # file was deleted
                previous_file.is_deleted = True
                previous_file.modified_at = datetime.now()
                print(f"FILE {previous_file.filename} IS MARKED AS DELETED")
                self.deleted_files.add(previous_file)

        for deleted_file in self.deleted_files.copy():
            # if file was deleted and then created again, it's not deleted anymore
            if deleted_file in self.local_files:
                print(f"FILE {deleted_file.filename} IS NO LONGER DELETED")
                self.deleted_files.remove(deleted_file)

    def __get_files_in_dir(self) -> list[File]:
        files = []

        try:
            filenames = [f for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path, f))]
            for filename in filenames:
                stat = os.stat(os.path.join(self.path, filename))
                files.append(File(
                    filename=filename,
                    created_at=datetime.fromtimestamp(stat.st_ctime),
                    modified_at=datetime.fromtimestamp(stat.st_mtime),
                    size=stat.st_size
                ))
        except Exception as e:
            print(e)  # TODO logging

        return files
