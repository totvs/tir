
import pandas as pd
import re
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from tir.technologies.core.logging_config import logger
from tir.technologies.core.config import ConfigLoader


class BaseDatabase:

    def __init__(self):
        self.config = ConfigLoader()


    def sqlalchemy_engine(self, database_driver="", dbq_oracle_server="", database_server="", database_port=1433, database_name="", database_user="", database_password="") -> Engine:
        """
        Cria e retorna um SQLAlchemy Engine para ODBC (SQL Server, Oracle, etc).
        """
        database_driver = self.config.database_driver if not database_driver else database_driver
        database_server = self.config.database_server if not database_server else database_server
        database_port = self.config.database_port if not database_port else database_port
        database_name = self.config.database_name if not database_name else database_name
        database_user = self.config.database_user if not database_user else database_user
        database_password = self.config.database_password if not database_password else database_password
        dbq_oracle_server = self.config.dbq_oracle_server if not dbq_oracle_server else dbq_oracle_server

        # SQL Server ODBC
        if database_driver.lower().startswith("odbc") or "sql server" in database_driver.lower():
            conn_str = (
                f"mssql+pyodbc://{database_user}:{database_password}@{database_server}:{database_port}/{database_name}"
                f"?driver={database_driver.replace(' ', '+')}"
            )
            return create_engine(conn_str)

        # Oracle ODBC (usando oracledb)
        elif "oracle" in database_driver.lower():
            # Exemplo de dbq_oracle_server: "host:port/service_name"
            if dbq_oracle_server:
                conn_str = (
                    f"oracle+oracledb://{database_user}:{database_password}@{dbq_oracle_server}"
                )
            else:
                host, service_name = database_server.split("/")
                
                conn_str = (
                    f"oracle+oracledb://{database_user}:{database_password}@{host}:{database_port}/?service_name={service_name}"
                )
            return create_engine(conn_str)

        else:
            raise ValueError("Database driver não suportado para SQLAlchemy.")


    def test_sqlalchemy_connection(self, engine: Engine):
        """
        Testa se a conexão está ativa.
        """
        try:
            with engine.connect() as conn:
                return True
        except SQLAlchemyError as e:
            logger().error(f"Erro ao testar conexão: {e}")
            return False


    def connect_database(self, query="", database_driver="", dbq_oracle_server="", database_server="", database_port=1521, database_name="", database_user="", database_password=""):
        engine = self.sqlalchemy_engine(database_driver, dbq_oracle_server, database_server, database_port, database_name, database_user, database_password)
        if self.test_sqlalchemy_connection(engine):
            logger().info('DataBase connection started')
        else:
            logger().info('DataBase connection is stopped')
        return engine


    def disconnect_database(self, engine: Engine):
        if engine:
            engine.dispose()
            logger().info('DataBase connection stopped')
        else:
            logger().info('DataBase connection already stopped')
            

    def query_execute(self, query, database_driver, dbq_oracle_server, database_server, database_port, database_name, database_user, database_password):
        """
        Executa uma query usando SQLAlchemy. Retorna um dicionário se SELECT, senão retorna número de linhas afetadas.
        """
        engine = self.connect_database(query, database_driver, dbq_oracle_server, database_server, database_port, database_name, database_user, database_password)
        try:
            with engine.connect() as conn:
                if query.strip().upper().startswith('SELECT'):
                    df = pd.read_sql_query(sql=text(query), con=conn)
                    return df.to_dict()
                else:
                    result = conn.execute(text(query))
                    conn.commit()
                    logger().info(f'{result.rowcount} row(s) affected')
                    return result.rowcount
        except SQLAlchemyError as e:
            logger().error(f'Erro ao executar query: {e}')
            return None
