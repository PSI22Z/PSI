import os
from datetime import datetime

from file_system.file import File


def get_files_in_dir(path) -> list[File]:
    filenames = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    files = []
    for filename in filenames:
        stat = os.stat(os.path.join(path, filename))
        files.append(File(
            filename=filename,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            size=stat.st_size
        ))
    return files


def save_file(path: str, file: File, content):
    path = os.path.join(path, file.filename)
    with open(path, 'wb') as f:
        f.write(content)
    os.utime(path, (file.modified_at.timestamp(), file.modified_at.timestamp()))


def read_file(path: str, filename: str) -> bytes:
    with open(os.path.join(path, filename), 'rb') as file:
        return file.read()
