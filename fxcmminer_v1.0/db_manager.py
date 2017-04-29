from event import DBReadyEvent
from log import Logger as log
import MySQLdb
import settings as s
import re
from datetime import datetime as dt
from bs4 import BeautifulSoup


class DatabaseManager(object):
    """
    The DatabaseManager provides an interface for interacting with the
    MariaDB database.
    """
    @staticmethod
    def write_data(event):
        """
        Writes the data to the database.
        """
        db = MySQLdb.connect(host=s.DB_HOST,
                              user=s.DB_USER,
                              passwd=s.DB_PASS)
        cur = db.cursor()
        data = event.data
        instrument = re.sub('[^A-Za-z0-9]+','', event.instrument)
        db_name = 'fxcm_bar_%s' % (instrument)
        tb_name = 'tbl_%s_%s' % (instrument, event.time_frame)
        table = "INSERT INTO %s.%s" % (db_name, tb_name)
        values = """ 
                 (date, bidopen, bidhigh, bidlow, bidclose,
                  askopen, askhigh, asklow, askclose, volume)
                 VALUES (%(date)s, %(bidopen)s, %(bidhigh)s, %(bidlow)s,
                  %(bidclose)s, %(askopen)s, %(askhigh)s, %(asklow)s,
                  %(askclose)s, %(volume)s)
                 """
        sql = table + values
        try:
            cur.executemany(sql, data)
            db.commit()
            log(instrument).debug("[IO] Data Written     : %s.%s" % (db_name, tb_name))
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            log(instrument).debug("[XX] Database Error   : %s.%s | %s" % (db_name, tb_name, e))
            return None
        
        db.close()

    @staticmethod
    def database_check(events_queue, event):
        """
        On first startup this method will create a new database and
        tables for each offer. 
        
        On second startup it will compare the database with the
        current offer and if the offer is not currenlty being tracked,
        it will create a new database and tables.
        """
        def _create_db(offer):
            """
            Creates databases and tables for any new offers
            """
            for o, time_frames in offer.iteritems():
                logfile = re.sub('[^A-Za-z0-9]+','',o)
                db_bar = 'fxcm_bar_%s' % (re.sub('[^A-Za-z0-9]+','',o))
                cur.execute("CREATE DATABASE IF NOT EXISTS %s;" % (db_bar))
                log(logfile).debug("[!!] Database Created : %s" % db_bar)
                for time_frame in time_frames:
                    tb_bar = 'tbl_%s_%s' % (re.sub('[^A-Za-z0-9]+','',o), time_frame)                                              
                    cur.execute("CREATE TABLE IF NOT EXISTS %s.%s ( \
                                 `date` DATETIME NOT NULL, \
                                 `bidopen` DECIMAL(19,6) NULL, \
                                 `bidhigh` DECIMAL(19,6) NULL, \
                                 `bidlow` DECIMAL(19,6) NULL, \
                                 `bidclose` DECIMAL(19,6) NULL, \
                                 `askopen` DECIMAL(19,6) NULL, \
                                 `askhigh` DECIMAL(19,6) NULL, \
                                 `asklow` DECIMAL(19,6) NULL, \
                                 `askclose` DECIMAL(19,6) NULL, \
                                 `volume` BIGINT NULL, \
                                PRIMARY KEY (`date`)) \
                                ENGINE=InnoDB;" % (db_bar, tb_bar))                
                    log(logfile).debug("[!!] Table Created    : %s" % tb_bar)

        db = MySQLdb.connect(host=s.DB_HOST,
                             user=s.DB_USER,
                             passwd=s.DB_PASS)
        cur = db.cursor()        
        fxoffer = event.fxoffer
        tracked = []
        cur.execute("SHOW DATABASES LIKE 'fxcm_bar_%';")
        if cur.fetchall() != ():
            for (db_name,) in cur:
                tracked.append(db_name.replace('fxcm_bar_', ''))
        else:
            _create_db(fxoffer)
            
        if tracked != []:
            for o in fxoffer:
                if re.sub('[^A-Za-z0-9]+','',o) not in tracked:
                    _create_db(fxoffer)

        events_queue.put(DBReadyEvent(fxoffer))
        
        db.close()

    @staticmethod
    def return_date(offer, time_frame):
        """
        Collects the latest date from the database, if no date is
        present, return a date from the catalog.
        """
        db = MySQLdb.connect(host=s.DB_HOST,
                             user=s.DB_USER,
                             passwd=s.DB_PASS)
        cur = db.cursor()  
        ins = re.sub('[^A-Za-z0-9]+','',offer)
        db_name = 'fxcm_bar_%s' % (ins)
        tb_name = 'tbl_%s_%s' % (ins, time_frame)
        try:
            cur.execute("SELECT `date` \
                          FROM %s.%s \
                          WHERE `date`=(SELECT MAX(`date`) \
                         FROM %s.%s);" % (db_name, tb_name,
                                          db_name, tb_name))
            date = cur.fetchone()[0]
        except TypeError:
            with open(s.XML_FILE, 'r') as f:
                soup = BeautifulSoup(f.read(), 'lxml-xml')
                for symbol in soup.find_all('symbol'):
                    if (symbol['price-stream'] == 'Default' and
                        symbol['name'] == offer):
                        for time in symbol.find_all('timeframe'):
                            if time['name'][:1] == time_frame[:1]:
                                initdate = time['start-date']
                                date = dt.strptime(initdate,
                                                   '%d.%m.%Y %H:%M:%S')
            try:
                date = date.replace(hour=16, minute=59)
            except NameError:
                # FXCM catalog not always upto date!
                date = dt(2007,1,1,00,00,00)
        
        db.close()

        return date
