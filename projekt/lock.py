import threading


# TODO rename

class Lock:
    def __init__(self):
        self.lock = threading.Lock()

    def acquire(self):
        self.lock.acquire()

    def release(self):
        self.lock.release()

    def locked(self):
        return self.lock.locked()


# TODO zalozyc locki? jak chronic dostep wielowatkowy?

lock = Lock()
