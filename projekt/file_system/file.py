from dataclasses import dataclass
from datetime import datetime


@dataclass
class File:
    filename: str
    created_at: datetime
    modified_at: datetime
    size: int
    is_deleted: bool = False

    def __eq__(self, other):
        return self.filename == other.filename

    def __hash__(self):
        return hash(self.filename)
