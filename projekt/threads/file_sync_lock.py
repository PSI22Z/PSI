import threading


# TODO chyba nie trzeba w kazdym miejscu tego locka stosowac

class FileSyncLock:
    def __init__(self):
        self.lock = threading.Lock()

    def acquire(self):
        self.lock.acquire()

    def release(self):
        if self.lock.locked():
            self.lock.release()


file_sync_lock = FileSyncLock()
