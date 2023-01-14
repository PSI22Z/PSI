import pickle
from typing import List

from file_system.file import File


def serialize(files: List[File]) -> bytes:
    return pickle.dumps(files)


def deserialize(msg: bytes) -> List[File]:
    return pickle.loads(msg)
