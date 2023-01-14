import threading


class DeletedFiles:
    def __init__(self):
        self.deleted_files = set()
        self.lock = threading.Lock()

    def add(self, file):
        self.lock.acquire()
        self.deleted_files.add(file)
        self.lock.release()

    def remove(self, file):
        self.lock.acquire()
        self.deleted_files.remove(file)
        self.lock.release()

    def to_list(self):
        return list(self.deleted_files)

    def copy(self):
        return self.deleted_files.copy()

    def __iter__(self):
        return self.deleted_files.__iter__()

    def __contains__(self, item):
        return self.deleted_files.__contains__(item)

    def __repr__(self):
        return self.deleted_files.__repr__()

    def __str__(self):
        return self.deleted_files.__str__()

    def __len__(self):
        return self.deleted_files.__len__()
