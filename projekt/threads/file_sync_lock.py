import threading


# TODO chyba nie trzeba w kazdym miejscu tego locka stosowac

class FileSyncLock:
    def __init__(self):
        self.lock = threading.Lock()

    def acquire(self):
        # print('acquire')
        self.lock.acquire()

    def release(self):
        # print('release if locked')
        if self.lock.locked():
            # print('release')
            self.lock.release()


file_sync_lock = FileSyncLock()
