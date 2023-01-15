import logging


def get_logger(logger_name):
    logging.basicConfig(filename="filesync.log",
                        filemode='a',
                        format='%(asctime)s.%(msecs)-3d %(levelname)-8s %(name)-18s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)

    return logging.getLogger(logger_name)
