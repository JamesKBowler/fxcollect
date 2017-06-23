import MySQLdb
from sqlalchemy import create_engine
from sqlalchemy import exc
from settings import DB_HOST, DB_USER, DB_PASS
import re

class DatabaseManager(object):
    """
    The DatabaseManager provides an interface for interacting with the
    MariaDB database.
    """
    def _datebase_cursor(self):
        db = MySQLdb.connect(
                host=DB_HOST,
                user=DB_USER,
                passwd=DB_PASS
        )
        cur = db.cursor()
        return db, cur

    def _name_conversion(self, instrument, time_frame):
        """
        Converts any instrument names into the database manager.
        Example: 
            'GBP/USD' | 'm1' becomes 'fxcm_bar_GBPUSD.tbl_GBPUSD_m1'
        """
        ins = re.sub('[^A-Za-z0-9]+','',instrument)
        db_name = 'fxcm_bar_%s' % (re.sub('[^A-Za-z0-9]+','',ins))
        tb_name = 'tbl_%s_%s' % (ins, time_frame)
        return db_name, tb_name
        
    def latest_dbdate(self, instrument, time_frame):
        """
        Collects the latest date from the database.
        """
        db, cur = self._datebase_cursor()
        db_name, tb_name = self._name_conversion(instrument, time_frame)
        try:
            cur.execute("SELECT `date` \
                          FROM %s.%s \
                          WHERE `date`=(SELECT MAX(`date`) \
                         FROM %s.%s);" % (db_name, tb_name,
                                          db_name, tb_name))
            self.latest_dbdate = cur.fetchone()[0]
        except TypeError:
            self.latest_dbdate = None        
        return self.latest_dbdate

    def get_databases(self):
        """        
        Returns a list of the current databases.
        """
        current_databases = []
        db, cur = self._datebase_cursor()
        cur.execute("SHOW DATABASES LIKE 'fxcm_bar_%';")
        if cur.fetchall() != ():
            for (db_name,) in cur:
                dbn = db_name.replace('fxcm_bar_', '')
                current_databases.append(dbn)
        cur.close()
        db.close()
        return current_databases

    def database_creation(self, offer, time_frames):
        """
        This method will create a new database and associated tables.
        """
        db, cur = self._datebase_cursor()
        db_bar = 'fxcm_bar_%s' % (re.sub('[^A-Za-z0-9]+','',offer))
        cur.execute("CREATE DATABASE IF NOT EXISTS %s;" % (db_bar))
        for time_frame in time_frames:
            tb_bar = 'tbl_%s_%s' % (
                re.sub('[^A-Za-z0-9]+','',offer), time_frame)                                              
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
        cur.close()
        db.close()

    def _drop_duplicates_from_dataframe(self, db_name, tb_name, data):
        """
        This ensures there are never any duplicate attempts written to
        the database. First a call is made to the database that matches
        the dateframe date range. Then each date in the DataFrame index
        is checked against the data base date range. Any postive matches
        are dropped fromt the DataFrame.
        """
        db, cur = self._datebase_cursor()
        cur.execute("SELECT date \
                     FROM %s.%s \
                     WHERE date >= '%s' and \
                     date <= '%s';" % (db_name, tb_name,
                                      str(data.index.min()),
                                      str(data.index.max())))
        db_dates = cur.fetchall()
        db_date_list = []
        if len(db_dates) != 0:
            for (date_,) in db_dates:
                db_date_list.append(date_)
            for db_date in db_date_list:
                if db_date in data.index:
                    data = data[data.index != db_date]
        cur.close()
        db.close()
        return data

    def write_to_db(self, event):
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
            event.instrument, event.time_frame)
        data = self._drop_duplicates_from_dataframe(
            db_name, tb_name, event.data)
        if not data.empty:
            engine = create_engine('mysql://%s:%s@%s/%s' % (
                DB_USER, DB_PASS, DB_HOST, db_name))
            try:
                data.to_sql(
                    name=tb_name, con=engine, if_exists='append')
            except exc.IntegrityError as e:
                print("[XX] Database Error   : %s.%s | %s" % (
                    db_name, tb_name, e))
                print("[XX] Database Error   : From : %s To : %s" % (
                    data.index.min(), data.index.max()))
