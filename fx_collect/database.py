import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb
from settings import DB_HOST, DB_USER, DB_PASS
import re


class DatabaseHandler(object):
    def __init__(self, broker):
        """
        The DatabaseManager provides an interface for interacting
        with the MariaDB database.
        """
        self.broker = broker

    def _datebase_cursor(self):
        """
        Creates a session and cursor
        """
        db = MySQLdb.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASS
        )
        cur = db.cursor()
        return db, cur

    def _name_conversion(self, instrument, time_frame=None):
        """
        Converts any instrument names into the database manager.
        Example: 
            'GBP/USD' | 'm1' becomes 'fxcm_bar_GBPUSD.tbl_GBPUSD_m1'
        """
        ins = re.sub('[^A-Za-z0-9]+','',instrument)
        db_name = "%s_bar_%s" % (self.broker, ins)
        if time_frame is not None:
            tb_name = 'tbl_%s_%s' % (ins, time_frame)
            return db_name, tb_name
        else: return db_name

    def return_extremity_dates(
        self, instrument, time_frame
    ):
        """
        Collects the latest date from the database.
        """
        db, cur = self._datebase_cursor()
        db_name, tb_name = self._name_conversion(
            instrument, time_frame)
        try:
            cur.execute("SELECT `date` \
                          FROM %s.%s \
                          WHERE `date`=(SELECT MIN(`date`) \
                         FROM %s.%s);" % (
                    db_name, tb_name, db_name, tb_name
                )
            )
            db_min = cur.fetchone()[0]
            cur.execute("SELECT `date` \
                          FROM %s.%s \
                          WHERE `date`=(SELECT MAX(`date`) \
                         FROM %s.%s);" % (
                    db_name, tb_name, db_name, tb_name
                )
            )
            db_max = cur.fetchone()[0]
            return db_min, db_max
        except TypeError: return False
        finally:
            cur.close()
            db.close()

    def get_databases(self):
        """        
        Returns a list of the current databases.
        """
        current_databases = []
        db, cur = self._datebase_cursor()
        if cur.execute("SHOW DATABASES LIKE '%s_bar_" % (
            self.broker) + "%';") != 0:
            for (db_name,) in cur.fetchall():
                dbn = db_name.replace('%s_bar_' % self.broker, '')
                current_databases.append(dbn)
        cur.close()
        db.close()
        return current_databases

    def create(self, instrument, time_frames):
        """
        This method will create a new database and associated tables.
        """
        databases = self.get_databases()
        db_name = self._name_conversion(instrument)
        db, cur = self._datebase_cursor()
        if (
            re.sub('[^A-Za-z0-9]+','',instrument
            ) not in databases
        ):
            cur.execute("CREATE DATABASE IF NOT EXISTS %s;" % (db_name))
        for time_frame in time_frames:            
            db_name, tb_name = self._name_conversion(
                instrument, time_frame)
            if not cur.execute(
                "SHOW TABLES FROM %s LIKE '%s';" % (db_name, tb_name)
            ):
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
                            ENGINE=InnoDB;" % (db_name, tb_name))
        db.close()

    def write(self, instrument, time_frame, data):
        """
        Writes data to the database.
        +---------------------+-----------+-----------+-----------+-----------+-----------+-----------+-----------+-----------+--------+
        | date                | bidopen   | bidhigh   | bidlow    | bidclose  | askopen   | askhigh   | asklow    | askclose  | volume |
        +---------------------+-----------+-----------+-----------+-----------+-----------+-----------+-----------+-----------+--------+
        | 2017-04-27 10:01:00 | 17.294000 | 17.296000 | 17.289000 | 17.290000 | 17.340000 | 17.340000 | 17.334000 | 17.335000 |    113 |
        | 2017-04-27 10:02:00 | 17.290000 | 17.298000 | 17.285000 | 17.295000 | 17.335000 | 17.342000 | 17.330000 | 17.340000 |    114 |
        | 2017-04-27 10:03:00 | 17.295000 | 17.301000 | 17.289000 | 17.299000 | 17.340000 | 17.347000 | 17.340000 | 17.344000 |     98 |
        | 2017-04-27 10:04:00 | 17.299000 | 17.300000 | 17.286000 | 17.295000 | 17.344000 | 17.345000 | 17.330000 | 17.340000 |    124 |
        | 2017-04-27 10:05:00 | 17.295000 | 17.295000 | 17.285000 | 17.292000 | 17.340000 | 17.340000 | 17.330000 | 17.336000 |    130 |
        | 2017-04-27 10:06:00 | 17.292000 | 17.292000 | 17.279000 | 17.292000 | 17.336000 | 17.336000 | 17.328000 | 17.332000 |     65 |
        | 2017-04-27 10:07:00 | 17.292000 | 17.304000 | 17.287000 | 17.298000 | 17.332000 | 17.348000 | 17.332000 | 17.345000 |    144 |
        | 2017-04-27 10:08:00 | 17.298000 | 17.306000 | 17.297000 | 17.302000 | 17.345000 | 17.350000 | 17.343000 | 17.346000 |     96 |
        | 2017-04-27 10:09:00 | 17.302000 | 17.303000 | 17.294000 | 17.294000 | 17.346000 | 17.346000 | 17.338000 | 17.338000 |     50 |
        | 2017-04-27 10:10:00 | 17.294000 | 17.296000 | 17.281000 | 17.291000 | 17.338000 | 17.338000 | 17.328000 | 17.333000 |     50 |
        """
        db_name, tb_name = self._name_conversion(
            instrument, time_frame)
        db, cur = self._datebase_cursor()
        insert = "REPLACE INTO %s.%s " % (db_name, tb_name)
        stmt = """(date, bidopen, bidhigh, bidlow, bidclose,
                  askopen, askhigh, asklow, askclose, volume
                  ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
        sql = insert + stmt
        try:
            cur.executemany(sql, data.tolist())
            db.commit()
        except pymysql.err.IntegrityError as e:
            print("[XX] Database Error   : %s.%s | %s" % (
                db_name, tb_name, e))
            print("[XX] Database Error   : %s, %s, %s, %s" % (
                instrument, time_frame,
                data['date'].min().item(), data['date'].max().item())
            )
        finally:
            cur.close()
            db.close()
