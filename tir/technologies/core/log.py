import time
import os
import numpy as nump
import pandas as panda

class Log:
    """
    This class is instantiated to create the log file and to append the results and failures to it.

    Usage:

    >>> # Instanted inside base.py:
    >>> self.log = Log(console=self.console_log)
    """
    def __init__(self, user="", station="", program="", program_date=time.strftime("%d/%m/%y %X"), version="", release="", database="", issue="", execution_id="", country="", console=False, folder=""):    
        self.console = console
        self.timestamp = time.strftime("%Y%m%d%H%M%S")

        self.user = user
        self.station = station
        self.program = program
        self.program_date = program_date
        self.version = version
        self.release = release
        self.database = database
        self.issue = issue
        self.execution_id = execution_id
        self.country = country
        self.initial_time = 0
        self.seconds = 0

        self.table_rows = []
        self.invalid_fields = []
        self.table_rows.append(self.generate_header())
        self.folder = folder

    def generate_header(self):
        """
        Generates the header line on the log file.

        Usage:

        >>> # Calling the method:
        >>> self.log.generate_header()
        """
        return ['Data','Usuário','Estação','Programa','Data Programa','Total CTs','Passou','Falhou', 'Segundos','Versão','Release', 'CTs Falhou', 'Banco de dados','Chamado','ID Execução','Pais']

    def new_line(self, result, message):
        """
        Appends a new line with data on log file.

        :param result: The result of the case.
        :type result: bool
        :param message: The message to be logged..
        :type message: str

        Usage:

        >>> # Calling the method:
        >>> self.log.new_line(True, "Success")
        """
        line = []
        total_cts = "1"
        passed = "1"
        failed = "0"
        if not result:
            passed = "0"
            failed = "1"
        line.extend([time.strftime("%d/%m/%y %X"), self.user, self.station, self.program, self.program_date, total_cts, passed, failed, self.seconds, self.version, self.release, message, self.database, self.issue, self.execution_id, self.country])
        self.table_rows.append(line)

    def save_file(self):
        """
        Writes the log file to the file system.

        Usage:

        >>> # Calling the method:
        >>> self.log.save_file()
        """
        if len(self.table_rows) > 0:
            data = nump.array(self.table_rows)
            if self.folder != "":
                path = self.folder+"\loginter_{}.csv".format(self.timestamp)
            else:
                path = "loginter_{}.csv".format(self.timestamp)
            df = panda.DataFrame(data, columns=data[0])
            df.drop(0, inplace=True)
            df.to_csv(path, index=False, sep=';', encoding='latin-1')

            if self.console:
                print('Arquivo {} gerado com sucesso!'.format(path))

    def set_seconds(self):
        """
        Sets the seconds variable through a calculation of current time minus the execution start time.

        Usage:

        >>> # Calling the method:
        >>> self.log.set_seconds()
        """
        self.seconds = time.time() - self.initial_time