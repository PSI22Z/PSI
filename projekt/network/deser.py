import datetime
from typing import List

from file_system.file import File
from utils.consts import ENCODING


def str_to_bool(s: str) -> bool:
    return s == 'True'


def serialize(files: List[File]) -> bytes:
    msg = bytearray()
    for file in files:
        msg.extend(
            f"{file.filename},{file.created_at.timestamp()},{file.modified_at.timestamp()},{file.size},{file.is_deleted};"
            .encode(ENCODING))
    return msg


def deserialize(msg: bytes, logger) -> List[File]:
    files = []
    try:
        for file in msg.decode(ENCODING).split(';')[:-1]:
            filename, created_at, modified_at, size, is_deleted = file.split(',')
            files.append(
                File(filename,
                     datetime.datetime.fromtimestamp(float(created_at)),
                     datetime.datetime.fromtimestamp(float(modified_at)),
                     int(size),
                     str_to_bool(is_deleted))
            )
    except Exception as e:
        logger.error(f"Error while deserializing: {e}")
    return files
