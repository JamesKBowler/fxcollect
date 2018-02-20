from .base import AbstractDatabase


class Database(AbstractDatabase):
    def __init__(self, broker):
        """
        The DatabaseManager provides an interface for interacting
        with the MariaDB database.
        """
        self.broker = broker
        dir = '/home/nonroot/.database_sec_master_credentials'
        with open(dir) as f:
            credentials = f.readlines()
        host, user, passwd = credentials[0].strip().split(':') 
        self._h = host
        self._u = user
        self._p = passwd

    def get_databases(self):
        """        
        Returns a list of databases.
        """
        current_databases = []
        query = "SHOW DATABASES LIKE '{0}_bar_%';".format(self.broker)
        result = self._execute_query(query)
        if result is not None:
            for (db_name,) in result:
                if len(db_name) > 1:
                    current_databases.append(db_name)
        return current_databases

    def get_tables(self, db_name):
        """        
        Returns a list tables.
        """
        current_tables = []
        query = "SHOW TABLES FROM {0};".format(db_name)
        result = self._execute_query(query)
        if result is not None:
            for (tb_name,) in result:
                if len(tb_name) > 1:
                    current_tables.append(tb_name)
        return current_tables

    def create(self, instrument, time_frames):
        """
        Create a new database and associated tables.
        """
        db_name = self.name_conversion(instrument=instrument)
        if db_name not in self.get_databases():
            self._execute_query(
                "CREATE DATABASE IF NOT EXISTS {};".format(db_name))
        for time_frame in time_frames:            
            tb_name = self.name_conversion(
                instrument, time_frame, True)
            if tb_name not in self.get_tables(db_name):
                self._execute_query(
                    """CREATE TABLE IF NOT EXISTS {0}.{1} (
                        `date` DATETIME NOT NULL,
                        `bidopen` DECIMAL(19,6) NULL,
                        `bidhigh` DECIMAL(19,6) NULL,
                        `bidlow` DECIMAL(19,6) NULL,
                        `bidclose` DECIMAL(19,6) NULL,
                        `askopen` DECIMAL(19,6) NULL,
                        `askhigh` DECIMAL(19,6) NULL,
                        `asklow` DECIMAL(19,6) NULL,
                        `askclose` DECIMAL(19,6) NULL,
                        `volume` BIGINT NULL,
                    PRIMARY KEY (`date`))
                    ENGINE=InnoDB;""".format(db_name, tb_name)
                )

    def extremity_dates(
        self, instrument, time_frame
    ):
        """
        Returns the earliest and latest date from the database.
        """
        db_name, tb_name = self.name_conversion(
            instrument, time_frame)
        query = """
            SELECT `date` 
            FROM (SELECT `date` 
                  FROM {0}.{1} 
                  ORDER BY `date` ASC LIMIT 1
                  ) a
            UNION
            SELECT `date` 
            FROM (SELECT `date` 
                  FROM {2}.{3} 
                  ORDER BY `date` DESC LIMIT 1
                  ) b;""".format(db_name, tb_name, db_name, tb_name)
        result = self._execute_query(query)
        if result:
            (dbmin,) = result[0]
            (dbmax,) = result[1]
            return dbmin, dbmax
        return False

    def write(self, instrument, time_frame, data):        
        db_name, tb_name = self.name_conversion(
            instrument, time_frame)        
        insert = "REPLACE INTO {0}.{1} ".format(db_name, tb_name)
        stmt = """(date, bidopen, bidhigh, bidlow, bidclose,
                  askopen, askhigh, asklow, askclose, volume
                  ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
        sql = insert + stmt
        self._execute_many(sql, data)
