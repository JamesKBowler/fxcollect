import logging
import logging.handlers

class Logger(object):
    def __init__(self, instrument):
        f = logging.Formatter(fmt='%(levelname)s:%(name)s: %(message)s '
            '(%(asctime)s; %(filename)s:%(lineno)d)',
            datefmt=None)  #"%Y-%m-%d %H:%M:%S.%f"
        handlers = [
            logging.handlers.RotatingFileHandler('logs/%s.log' % instrument, encoding='utf8',
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
        msgattr = "%s : %s %s" % msg[0:3]
        a = msg[3].strftime('%Y/%m/%d %H:%M')
        b = msg[4].strftime('%Y/%m/%d %H:%M') 
        log = " ".join([msgattr, a , b])
        self.root_logger.debug(log)
