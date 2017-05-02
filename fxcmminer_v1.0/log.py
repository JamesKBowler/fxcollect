import logging
from logging import DEBUG
from settings import LOG_DIR
import re

class Logger(object):
    def __init__(self, filename):
        
        fn = '%s/%s.log' % (LOG_DIR, re.sub('[^A-Za-z0-9]+','',filename))
        
        logging.basicConfig(filename=fn,level=DEBUG)

    def debug(self, message):
        logging.debug(message)
