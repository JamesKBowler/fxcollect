import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb
import re

from abc import ABCMeta


class AbstractDatabase(object):
    
    __metaclass__ = ABCMeta
        
    def _db_connection(self):
        return MySQLdb.connect(
                host=self._h, user=self._u, passwd=self._p
            )

    def _execute_query(self, query):
        connection = self._db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            if results:
                return results
            else:
                return None
        finally:
            cursor.close()
            connection.close()

    def _execute_many(self, stmt, data):
        connection = self._db_connection()
        cursor = connection.cursor()
        try:
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
        db_name = "{0}_bar_{1}".format(self.broker, ins)
        tb_name = "tbl_{0}_{1}".format(ins, time_frame)
        if time_frame is None:
            return db_name
        elif table is not False:
            return tb_name
        else:
            return db_name, tb_name