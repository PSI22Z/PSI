import os
from datetime import datetime

from file_system.deleted_files import DeletedFiles
from file_system.file import File


# TODO zrobic z tego klasę?

class FileSystem:
    def __init__(self, path):
        if not os.path.isdir(path):
            raise Exception('Not a directory')
        self.path = path
        self.deleted_files = DeletedFiles()
        self.local_files = self.get_files_in_dir()

    def get_files_in_dir(self) -> list[File]:
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
