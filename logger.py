import logging

logging.basicConfig(level=logging.DEBUG, filename='main_log.log', format='%(asctime)s %(levelname)s:%(message)s')


def log(text):
    """
    Функция записи логов

    :param text: текст лога
    """
    logging.info(text)
