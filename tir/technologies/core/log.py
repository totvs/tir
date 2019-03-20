import time
import os
import numpy as nump
import pandas as panda
import uuid
import csv
import inspect
from datetime import datetime

class Log:
    """
    This class is instantiated to create the log file and to append the results and failures to it.

    Usage:

    >>> # Instanted inside base.py:
    >>> self.log = Log()
    """
    def __init__(self, user="", station="", program="", program_date=time.strftime("01/01/1980 12:00:00"), version="", release="", database="", issue="", execution_id="", country="", folder="", test_type="TIR"):
        self.timestamp = time.strftime("%Y%m%d%H%M%S")

        self.user = user
        self.station = station
        self.program = program
        self.program_date = program_date
        self.version = version
        self.release = release
        self.database = database
        self.initial_time = datetime.today()
        self.seconds = 0

        self.table_rows = []
        self.invalid_fields = []
        self.table_rows.append(self.generate_header())
        self.folder = folder
        self.test_type = test_type
        self.issue = issue
        self.execution_id = execution_id
        self.country = country

    def generate_header(self):
        """
        Generates the header line on the log file.

        Usage:

        >>> # Calling the method:
        >>> self.log.generate_header()
        """
        return ['Data','Usuário','Estação','Programa','Data Programa','Total CTs','Passou','Falhou', 'Segundos','Versão','Release', 'CTs Falhou', 'Banco de dados','Chamado','ID Execução','Pais', "Tipo de Teste"]

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
        total_cts = 1
        passed = 1 if result else 0
        failed = 0 if result else 1

        line.extend([time.strftime("%d/%m/%Y %X"), self.user, self.station, self.program, self.program_date, total_cts, passed, failed, self.seconds, self.version, self.release, message, self.database, self.issue, self.execution_id, self.country, self.test_type])
        self.table_rows.append(line)

    def save_file(self, filename):
        """
        Writes the log file to the file system.

        Usage:

        >>> # Calling the method:
        >>> self.log.save_file()
        """
        
        log_file = f"{self.user}_{uuid.uuid4().hex}_auto.csv"
                
        if len(self.table_rows) > 0:
            try:
                if self.folder:
                    path = f"{self.folder}\\{self.station}\\{log_file}"
                    os.makedirs(f"{self.folder}\\{self.station}")
                else:
                    path = f"Log\\{self.station}\\{log_file}"
                    os.makedirs(f"Log\\{self.station}")
            except OSError:
                pass
            
            testcases = self.list_of_testcases()

            if len(self.table_rows[1:]) == len(testcases):
                with open(path, mode="w", newline="") as csv_file:
                    csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                    for line in self.table_rows:
                        csv_writer.writerow(line)

                print(f"Log file created successfully: {path}")

    def set_seconds(self):
        """
        Sets the seconds variable through a calculation of current time minus the execution start time.

        Usage:

        >>> # Calling the method:
        >>> self.log.set_seconds()
        """
        delta = datetime.today() - self.initial_time
        self.seconds = round(delta.total_seconds(), 2)

    def list_of_testcases(self):
        """
        Returns a list of test cases from suite 
        """
        runner = next(iter(list(filter(lambda x: "runner.py" in x.filename, inspect.stack()))))
        return list(runner.frame.f_locals['test'])