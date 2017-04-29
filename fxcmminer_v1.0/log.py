import logging
from logging import DEBUG

class Logger(object):
    def __init__(self, filename):
        self.filename = 'logs/%s.log' % filename
        logging.basicConfig(filename=self.filename,level=DEBUG)

    def debug(self, message):
        logging.debug(message)
