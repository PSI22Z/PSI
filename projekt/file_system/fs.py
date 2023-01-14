import os
from datetime import datetime

from file_system.file import File

# TODO zrobic z tego klasę?


def get_files_in_dir(path) -> list[File]:
    files = []

    try:
        filenames = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        for filename in filenames:
            stat = os.stat(os.path.join(path, filename))
            files.append(File(
                filename=filename,
                created_at=datetime.fromtimestamp(stat.st_ctime),
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                size=stat.st_size
            ))
    except Exception as e:
        print(e)  # TODO logging

    return files


def save_file(path: str, file: File, content):
    try:
        path = os.path.join(path, file.filename)
        with open(path, 'wb') as f:
            f.write(content)
        os.utime(path, (file.modified_at.timestamp(), file.modified_at.timestamp()))
    except Exception as e:
        print(e)  # TODO logging


def read_file(path: str, filename: str) -> bytes | None:
    try:
        with open(os.path.join(path, filename), 'rb') as file:
            return file.read()
    except Exception as e:
        print(e)  # TODO logging
        return None


def delete_file(path: str, filename: str):
    try:
        os.remove(os.path.join(path, filename))
    except Exception as e:
        print(e)  # TODO logging
