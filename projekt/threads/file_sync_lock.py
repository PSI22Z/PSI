import threading


# TODO rename

# TODO chyba nie trzeba w kazdym miejscu tego locka stosowac

class FileSyncLock:
    def __init__(self):
        self.lock = threading.Lock()

    def acquire(self):
        self.lock.acquire()

    def release(self):
        if self.lock.locked():
            self.lock.release()


# TODO zalozyc locki? jak chronic dostep wielowatkowy?

file_sync_lock = FileSyncLock()
