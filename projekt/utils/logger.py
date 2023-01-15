import logging
import sys


def get_logger(logger_name):
    file_handler = logging.FileHandler('filesync.log', mode='a')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]

    logging.basicConfig(handlers=handlers,
                        format='%(asctime)s.%(msecs)-3d %(levelname)-8s %(name)-18s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)

    return logging.getLogger(logger_name)
