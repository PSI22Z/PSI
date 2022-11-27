import socket
import sys

try:
    ADDRESS = socket.gethostbyname(sys.argv[1])
except socket.gaierror:
    print(f'Server "{sys.argv[1]}" is not running')
    quit()

PORT = 8888
BUFFER_SIZE = 1024


def send_datagram(udp_socket, size):
    message = str.encode('a' * size)
    udp_socket.sendto(message, (ADDRESS, PORT))


def main():
    udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    # Wynik 65507 Bajtów
    for i in range(1, 100000):
        send_datagram(udp_socket, i)
        print(f"sent datagram with size: {i} bytes")


if __name__ == '__main__':
    main()
