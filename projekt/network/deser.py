import datetime
from typing import List

from file_system.file import File
from utils.consts import ENCODING


def serialize(files: List[File]) -> bytes:
    msg = bytearray()
    for file in files:
        msg.extend(
            f"{file.filename},{file.created_at.timestamp()},{file.modified_at.timestamp()},{file.size},{file.is_deleted};"
            .encode(ENCODING))
    print(msg)
    return msg


def deserialize(msg: bytes) -> List[File]:
    files = []
    print(msg)
    for file in msg.decode(ENCODING).split(';')[:-1]:
        filename, created_at, modified_at, size, is_deleted = file.split(',')
        files.append(
            File(filename,
                 datetime.datetime.fromtimestamp(created_at),
                 datetime.datetime.fromtimestamp(modified_at),
                 size,
                 is_deleted)
        )
    print(files)
    return files
