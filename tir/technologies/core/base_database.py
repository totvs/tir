from tir.technologies.core.base import Base
from tir.technologies.webapp_internal import WebappInternal
import pandas as pd
import pyodbc
import re


class BaseDatabase(Base):

    def __init__(self):
        super().__init__(autostart=False)
        self.webapp_internal = WebappInternal(autostart=False)
        self.restart_counter = self.webapp_internal.restart_counter

    def odbc_connect(self, driver_database=None, server_database=None, name_database=None, user_database=None, password_database=None):
        """
        :return:
        """
        connection = None
        
        driver_database = self.config.driver_database if not driver_database else driver_database
        server_database = self.config.server_database if not server_database else server_database
        name_database = self.config.name_database if not name_database else name_database
        user_database = self.config.user_database if not user_database else user_database
        password_database = self.config.password_database if not password_database else password_database

        self.check_pyodbc_drivers(driver_database)

        try:
            connection = pyodbc.connect(f'DRIVER={driver_database}; server={server_database}; database={name_database}; uid={user_database}; pwd={password_database}')
        except Exception as error:
            self.webapp_internal.restart_counter = 3
            self.webapp_internal.log_error(str(error))

        return connection

    def test_odbc_connection(self, connection):
        """
        :param connection:
        :return: cursor attribute if connection ok else return False
        """
        try:
            return connection.cursor()
        except:
            return False

    def connect_database(self, driver_database=None, server_database=None, name_database=None, user_database=None, password_database=None):

        connection = self.odbc_connect(driver_database, server_database, name_database, user_database, password_database)

        if self.test_odbc_connection(connection):
            print('DataBase connection started')
        else:
            print('DataBase connection is stopped')

        return connection

    def disconnect_database(self, connection):

        if not connection:
            connection = self.odbc_connect()

        cursor = self.test_odbc_connection(connection)
        if cursor:
            cursor.close()
            connection.close()
            if not self.test_odbc_connection(connection):
                print('DataBase connection stopped')
        else:
            print('DataBase connection already stopped')

    def check_pyodbc_drivers(self, driver_database):
        if not next(iter(list(filter(lambda x: x == driver_database, pyodbc.drivers()))), None):
            error_message = f"Driver: '{driver_database}' isn't a valid driver name!"
            self.webapp_internal.restart_counter = 3
            self.webapp_internal.log_error(error_message)

    def query_execute(self, query, driver_database, server_database, name_database, user_database, password_database):
        """
        Return a dictionary if the query statement is a SELECT otherwise print a number of row 
        affected in case of INSERT|UPDATE|DELETE statement.

        .. note::  
            Default Database information is in config.json another way is possible put this in the QueryExecute method parameters:
            Parameters:
                "DriverDB": "",
                "ServerDB": "",
                "NameDB": "",
                "UserDB": "",
                "PasswordDB": ""

        .. note::        
            Must be used an ANSI default SQL statement.
        
        :param query: ANSI SQL estatement query
        :type query: str
        :param driver_database: ODBC Driver database name
        :type driver_database: str
        :param server_database: Database Server Name
        :type server_database: str
        :param name_database: Database Name
        :type name_database: str
        :param user_database: User Database Name
        :type user_database: str
        :param password_database: Database password
        :type password_database: str
        Usage:
        >>> # Call the method:
        >>> self.oHelper.QueryExecute("SELECT * FROM SA1T10")
        >>> self.oHelper.QueryExecute("SELECT * FROM SA1T10", driver_database="NOME_DO_DRIVER_ODBC", server_database="NOME_DO_SERVER", name_database="NOME_DO_BANCO", user_database="sa", password_database="123456")
        """
        connection = self.connect_database(driver_database, server_database, name_database, user_database, password_database)
        
        if re.findall(r'^(SELECT)', query.upper()):
            df = pd.read_sql(sql=query, con=connection)
            return (df.to_dict())
        elif re.findall(r'^(UPDATE|DELETE|INSERT)', query.upper()):
            self.cursor_execute(query, connection)
        else:
            self.webapp_internal.log_error(f"Not a valid query in {query}")

    def cursor_execute(self, query, connection):
        cursor = connection.cursor()
        try:
            rowcount = cursor.execute(query).rowcount
        except Exception as error:
            self.webapp_internal.log_error(str(error))
        print(f'{rowcount} row(s) affected')
        connection.commit()
