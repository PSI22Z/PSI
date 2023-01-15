from time import sleep

import netifaces


def get_ip_address(network_interface):
    return netifaces.ifaddresses(network_interface)[netifaces.AF_INET][0]['addr']


def get_broadcast_address(network_interface):
    return netifaces.ifaddresses(network_interface)[netifaces.AF_INET][0]['broadcast']


def safe_sleep(seconds, should_stop_func):
    for _ in range(seconds):
        if should_stop_func():
            return
        sleep(1)
