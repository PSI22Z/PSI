import os
from itertools import cycle

from utils.consts import ENCODING


def xor(data):
    key = bytes(os.getenv('SECRET_KEY'), ENCODING)
    return bytearray(c ^ k for c, k in zip(data, cycle(key)))
