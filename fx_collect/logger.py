import logging
import logging.handlers

class Logger(object):
    def __init__(self):
        f = logging.Formatter(fmt='%(levelname)s:%(name)s: %(message)s '
            '(%(asctime)s; %(filename)s:%(lineno)d)',
            datefmt="%Y-%m-%d %H:%M:%S")
        handlers = [
            logging.handlers.RotatingFileHandler('rotated.log', encoding='utf8',
                maxBytes=100000, backupCount=1),
            logging.StreamHandler()
        ]
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG)
        for h in handlers:
            h.setFormatter(f)
            h.setLevel(logging.DEBUG)
            self.root_logger.addHandler(h)

    def _debug(self, *msg):
        msgtype = msg[0]
        msgattr = "%s : %s %s" % msg[0:3]
        a = msg[4].strftime('%Y/%m/%d %H:%M')
        b = msg[5].strftime('%Y/%m/%d %H:%M') 
        log = " ".join([msgtype, msgattr, a , b])
        self.root_logger.debug(log)
