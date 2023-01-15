from time import sleep

import netifaces

from utils.consts import BUFF_SIZE


def get_ip_address(network_interface):
    return netifaces.ifaddresses(network_interface)[netifaces.AF_INET][0]['addr']


def get_broadcast_address(network_interface):
    return netifaces.ifaddresses(network_interface)[netifaces.AF_INET][0]['broadcast']


def recvall(conn):
    data = bytearray()
    while True:
        part = conn.recv(BUFF_SIZE)
        if not len(part):
            break
        data.extend(part)
    return data


def safe_sleep(seconds, should_stop_func):
    for _ in range(seconds):
        if should_stop_func():
            return
        sleep(1)
