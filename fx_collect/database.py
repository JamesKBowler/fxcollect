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
        self.databases = {}
        self.update_securities_dict()
        
    def update_securities_dict(self):
        for database in self.get_databases():
            self.databases[database] = self.get_tables(database)
        
    def _execute_query(self, query):
        try:
            connection = MySQLdb.connect(
                host=DB_HOST, user=DB_USER, passwd=DB_PASS
            )
            cursor = connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            if results: return results
            else: return None
        finally:
            cursor.close()
            connection.close()
            
    def _execute_many(self, stmt, data):
        try:
            connection = MySQLdb.connect(
                host=DB_HOST, user=DB_USER, passwd=DB_PASS
            )
            cursor = connection.cursor()
            cursor.executemany(stmt, data)
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    def name_conversion(self, instrument, time_frame=None, table=False):
        """
        Converts any instrument names into the database manager.
        Example: 
            'GBP/USD' | 'm1' becomes 'fxcm_bar_GBPUSD.tbl_GBPUSD_m1'
        """
        ins = re.sub('[^A-Za-z0-9]+','',instrument)
        db_name = "%s_bar_%s" % (self.broker, ins)
        tb_name = 'tbl_%s_%s' % (ins, time_frame)
        if time_frame is None:
            return db_name
        elif table is not False:
            return tb_name
        else:
            return db_name, tb_name

    def get_databases(self):
        """        
        Returns a list of the current databases.
        """
        current_databases = []
        query = """
                SHOW DATABASES LIKE '%s_bar_""" % (
                self.broker) + "%';"
        result = self._execute_query(query)
        if result is not None:
            for (db_name,) in result:
                if len(db_name) > 1:
                    current_databases.append(db_name)
        return current_databases

    def get_tables(self, db_name):
        """        
        Returns a list of the current databases.
        """
        current_tables = []
        query = """
                SHOW TABLES FROM %s;""" % (
                db_name)
        result = self._execute_query(query)
        if result is not None:
            for (tb_name,) in result:
                if len(tb_name) > 1:
                    current_tables.append(tb_name)
        return current_tables

    def get_start_datetime(self, instrument, dtnow):
        db_name, tb_name = self.name_conversion(
            instrument, 'm1')
        to_date = dtnow.replace(second=0,microsecond=0)
        fm_date = to_date.replace(hour=0,minute=0)
        query = """
            SELECT `date` 
            FROM (SELECT `date` 
                  FROM %s.%s 
                  WHERE `date` >= '%s' AND `date` <= '%s'
                  ORDER BY `date` ASC LIMIT 1) a;""" % (
              db_name, tb_name, fm_date, to_date)
        result = self._execute_query(query)
        if result:
            (dbmin,) = result
            return dbmin
        else: return False
        
    def return_extremity_dates(
        self, instrument, time_frame
    ):
        """
        returns the earliest and latest datetime.
        """
        db_name, tb_name = self.name_conversion(
            instrument, time_frame)
        query = """
            SELECT `date` 
            FROM (SELECT `date` 
                  FROM %s.%s 
                  ORDER BY `date` ASC LIMIT 1
                  ) a
            UNION
            SELECT `date` 
            FROM (SELECT `date` 
                  FROM %s.%s 
                  ORDER BY `date` DESC LIMIT 1
                  ) b;""" % (
            db_name, tb_name, db_name, tb_name)
        result = self._execute_query(query)
        if result:
            (dbmin,) = result[0]
            (dbmax,) = result[1]
            return dbmin, dbmax
        else: return False

    def create(self, instrument, time_frames):
        """
        This method will create a new database and associated tables.
        """
        db_name = self.name_conversion(instrument=instrument)
        if db_name not in self.databases:
            self._execute_query("CREATE DATABASE IF NOT EXISTS %s;" % (db_name))
        for time_frame in time_frames:            
            tb_name = self.name_conversion(
                instrument, time_frame, True)
            if tb_name not in self.databases[db_name]:
                self._execute_query("CREATE TABLE IF NOT EXISTS %s.%s ( \
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

        self.update_securities_dict()

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
        db_name, tb_name = self.name_conversion(
            instrument, time_frame)        
        insert = "REPLACE INTO %s.%s " % (db_name, tb_name)
        stmt = """(date, bidopen, bidhigh, bidlow, bidclose,
                  askopen, askhigh, asklow, askclose, volume
                  ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
        sql = insert + stmt
        self._execute_many(sql, data.tolist())
        
