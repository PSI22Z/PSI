from time import sleep
from typing import List, Tuple

import netifaces

from file_system.file import File


def get_ip_address(network_interface):
    return netifaces.ifaddresses(network_interface)[netifaces.AF_INET][0]['addr']


def get_broadcast_address(network_interface):
    return netifaces.ifaddresses(network_interface)[netifaces.AF_INET][0]['broadcast']


def safe_sleep(seconds, should_stop_func):
    for _ in range(seconds):
        if should_stop_func():
            return
        sleep(1)


def get_files_stats(files: List[File]) -> Tuple[int, int]:
    deleted = 0
    not_deleted = 0
    for file in files:
        if file.is_deleted:
            deleted += 1
        else:
            not_deleted += 1
    return not_deleted, deleted
