from tir.technologies.core.base import Base
from tir.technologies.webapp_internal import WebappInternal

import pyodbc

class BaseDatabase(Base):

    def __init__(self):
        super().__init__(autostart=False)
        self.webapp_internal = WebappInternal(autostart=False)
        self.restart_counter = self.webapp_internal.restart_counter

    def odbc_connect(self):
        """
        :return:
        """
        connection = None
        
        driver_database = self.config.driver_database
        server_database = self.config.server_database
        name_database = self.config.name_database
        user_database = self.config.user_database
        password_database = self.config.password_database

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

    def connect_database(self):

        connection = self.odbc_connect()

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
        error_message = f"Driver: '{driver_database}' isn't a valid driver name!"
        if not next(iter(list(filter(lambda x: x == driver_database, pyodbc.drivers()))), None):
            self.webapp_internal.restart_counter = 3
            self.webapp_internal.log_error(error_message)
