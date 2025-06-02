import time
import os
import sys
from pathlib import Path
import numpy as nump
import pandas as panda
import uuid
import csv
import inspect
import re
import platform
import requests
import json
from datetime import datetime
from tir.technologies.core.config import ConfigLoader
from tir.technologies.core.logging_config import logger

class Log:
    """
    This class is instantiated to create the log file and to append the results and failures to it.

    Usage:

    >>> # Instanted inside base.py:
    >>> self.log = Log()
    """
    def __init__(self, suite_datetime="", user="", station="", program="", program_date=("19800101"), version="", release="", database="", issue="", execution_id="", country="", folder="", test_type="TIR", config_path=""):
        self.timestamp = time.strftime("%Y%m%d%H%M%S")

        today = datetime.today()

        self.config = ConfigLoader(config_path)
        self.user = user
        self.station = station
        self.program = program
        self.program_date = program_date
        self.version = version
        self.release = release
        self.database = database
        self.initial_time = datetime.today()
        self.testcase_initial_time = datetime.today()
        self.seconds = 0
        self.testcase_seconds = 0
        self.suite_datetime = suite_datetime

        self.table_rows = []
        self.test_case_log = []
        self.csv_log = []
        self.invalid_fields = []
        self.table_rows.append(self.generate_header())
        self.folder = folder
        self.test_type = test_type
        self.issue = self.config.issue
        self.execution_id = self.config.execution_id
        self.country = self.config.country
        self.start_time = None
        self.end_time = None
        self.ct_method = ""
        self.ct_number = ""
        self.so_type = platform.system()
        self.so_version = f"{self.so_type} {platform.release()}"
        self.build_version = ""
        self.lib_version = ""
        self.webapp_version = ""
        self.date = today.strftime('%Y%m%d')
        self.hour = today.strftime('%H:%M:%S')
        self.last_exec = today.strftime('%Y%m%d%H%M%S%f')[:-3]
        self.hash_exec = ""
        self.test_case = self.list_of_testcases()
        self.finish_testcase = []
        self.testcase_generate_log = []

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
        printable_message = self.printable_message(message)

        if not self.suite_datetime:
            self.suite_datetime = time.strftime("%d/%m/%Y %X")
        if self.get_testcase_stack() not in self.test_case_log:
            line.extend([self.suite_datetime, self.user, self.station, self.program, self.program_date, total_cts, passed, failed, self.seconds, self.version, self.release, printable_message, self.database, self.issue, self.execution_id, self.country, self.test_type])
            self.table_rows.append(line)
            self.test_case_log.append(self.get_testcase_stack())

    def save_file(self):
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
                    path = Path(self.folder, self.station+"_v6")
                    os.makedirs(path)
                else:
                    path = Path("/tmp/Log", self.station) if sys.platform.lower() == "linux" else Path("Log", self.station)
                    os.makedirs(path)
            except OSError:
                pass

            self.checks_empty_line()

            with open( Path(path, log_file), mode="w", newline="", encoding="windows-1252") as csv_file:
                csv_writer_header = csv.writer(csv_file, delimiter=';', quoting=csv.QUOTE_NONE)
                csv_writer_header.writerow(self.table_rows[0])
                csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                for line in self.table_rows[1:]:
                    logger().debug(f'CSV Line: {line}')
                    csv_writer.writerow(line)

            logger().debug(f"Log file created successfully: {os.path.join(path, log_file)}")

                            
            self.csv_log.append(self.get_testcase_stack())

    def log_exec_file(self):
        """
        [Internal]
        """

        before_modification = None

        log_exec_file = "log_exec_file.txt"

        logger().debug(f"Writing {log_exec_file}")

        logger().debug(f"Script folder source: {os.getcwd()}")

        if os.path.exists(log_exec_file):
            before_modification = os.path.getmtime(log_exec_file)
            logger().debug(f"Before modification: {datetime.fromtimestamp(os.path.getmtime(log_exec_file)).strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            logger().debug(f"{log_exec_file} file doesn't exist.")

        logger().debug(f"Creating {log_exec_file} file")
        open("log_exec_file.txt", "w")

        after_modification = os.path.getmtime(log_exec_file)
        logger().debug(f"After modification: {datetime.fromtimestamp(os.path.getmtime(log_exec_file)).strftime('%Y-%m-%d %H:%M:%S')}")

        if before_modification != after_modification:
            logger().debug(f"{log_exec_file} file update successfully")

    def has_csv_condition(self):

        return (self.get_testcase_stack() not in self.testcase_generate_log) or ((self.get_testcase_stack() == "setUpClass") and self.checks_empty_line())

    def set_seconds(self, initial_time):
        """
        Sets the seconds variable through a calculation of current time minus the execution start time.

        Usage:

        >>> # Calling the method:
        >>> self.log.set_seconds()
        """
        delta = datetime.today() - initial_time
        return round(delta.total_seconds(), 2)

    def list_of_testcases(self):
        """
        Returns a list of test cases from suite 
        """
        runner = next(iter(list(filter(lambda x: "runner.py" in x.filename, inspect.stack()))), None)

        if runner:
            try:
                return list(filter(lambda x: x is not None, list(runner.frame.f_locals['test']._tests)))
            except KeyError:
                return []
        else:
            return []

    def get_testcase_stack(self):
        """
        Returns a string with the current testcase name
        [Internal]
        """
        return next(iter(list(map(lambda x: x.function, filter(lambda x: re.search('setUpClass|test_|tearDownClass', x.function), inspect.stack())))), None)

    def checks_empty_line(self):
        """
        Checks if the log file is not empty.
        03 - 'Programa'  10 - 'Release' 14 - 'ID Execução' 15 - 'Pais' 
        [Internal]
        """

        logger().debug('Checking empty default log info')

        table_rows_has_line = False

        for row in range(0, len(self.table_rows)):
            if self.table_rows[row][3] == '':
                self.table_rows[row][3] = self.get_program_name()

            if self.table_rows[row][10] == '':
                self.table_rows[row][10] = self.config.release if self.config.release else '12.1.2410'

            if self.table_rows[row][15] == '':
                self.table_rows[row][15] = self.config.country if self.config.country else 'BRA'

            if self.table_rows[row][7] == 1:
                if self.table_rows[row][11] == '':
                    self.table_rows[row][11] = 'NO DATA'

            if self.table_rows[row][12] == '':
                self.table_rows[row][12] = 'MSSQL'

            if len(self.table_rows) > 1:
                for x in [ 3, 10, 15 ]:
                    if (self.table_rows[row][x]):
                        table_rows_has_line = True
                    else:
                        table_rows_has_line = False
                        break
                if self.config.smart_test and self.table_rows[row][14] and table_rows_has_line:
                    table_rows_has_line = True
                elif self.config.smart_test:
                    table_rows_has_line = False

        return table_rows_has_line

    def generate_result(self, result, message):
        """
        Generate a result of testcase and export to a json.

        :param result: The result of the case.
        :type result: bool
        :param message: The message to be logged..
        :type message: str

        Usage:

        >>> # Calling the method:
        >>> self.log.generate_result(True, "Success")
        """
        printable_message = self.printable_message(message)

        if not self.suite_datetime:
            self.suite_datetime = time.strftime("%d/%m/%Y %X")

        self.generate_json(self.generate_dict(result, printable_message))

    def get_file_name(self, file_name):
        """
        Returns a Testsuite name
        """
        testsuite_stack = next(iter(list(filter(lambda x: file_name in x.filename.lower(), inspect.stack()))), None)

        if testsuite_stack:

            if '/' in testsuite_stack.filename:
                split_character = '/'
            else:
                split_character = '\\'

            return testsuite_stack.filename.split(split_character)[-1].split(".")[0]
        else:
            return ""

    def generate_dict(self, result, message):
        """
        Returns a dictionary with the log information
        """
        log_version = "20200814"

        dict_key = {
            "APPVERSION": self.build_version,
            "CLIVERSION": self.webapp_version,
            "COUNTRY": self.country,
            "CTMETHOD": self.ct_method,
            "CTNUMBER": self.ct_number,
            "DBACCESS": "",
            "DBTYPE": self.database,
            "DBVERSION": "",
            "EXECDATE": self.date,
            "EXECTIME": self.hour,
            "FAIL": 0 if result else 1,
            "FAILMSG": message,
            "IDENTI": self.issue,
            "IDEXEC": self.config.execution_id,
            "LASTEXEC": self.last_exec,
            "LIBVERSION": self.lib_version,
            "OBSERV": "",
            "PASS": 1 if result else 0,
            "PROGDATE": self.program_date,
            "PROGRAM": self.program,
            "PROGTIME": "00:00:00",
            "RELEASE": self.release,
            "SECONDSCT": self.testcase_seconds,
            "SOTYPE": self.so_type,
            "SOVERSION": self.so_version,
            "STATION": self.station,
            "STATUS": "", # ???
            "TESTCASE": self.get_file_name('testcase'),
            "TESTSUITE": self.get_file_name('testsuite'),
            "TESTTYPE": "1",
            "TOKEN": "TIR4541c86d1158400092A6c7089cd9e9ae-2020", # ???
            "TOOL": self.test_type,
            "USRNAME": self.user,
            "VERSION": self.version
        }

        return dict_key

    def generate_json(self, dictionary):
        """
        """
        server_address1 = self.config.logurl1
        server_address2 = self.config.logurl2

        success = False

        data = dictionary

        json_data = json.dumps(data)

        endtime = time.time() + 30

        while (time.time() < endtime and not success):

            success = self.send_request(server_address1, json_data)

            if not success:
                success = self.send_request(server_address2, json_data)

            time.sleep(10)

        if not success:
            self.save_json_file(json_data)

    def send_request(self, server_address, json_data):
        """
        Send a post request to server
        """
        success = False
        response = None
        headers = {'content-type': 'application/json'}

        try:
            response = requests.post(server_address.strip(), data=json_data, headers=headers)
        except:
            pass

        if response is not None:
            if response.status_code == 200:
                logger().debug("Log de execucao enviado com sucesso!")
                success = True
            elif response.status_code == 201 or response.status_code == 204:
                logger().debug("Log de execucao enviado com sucesso!")
                success = True
            else:
                self.save_response_log(response, server_address, json_data)
                return False
        else:
            return False

        return success

    def save_response_log(self, response, server_address, json_data):
        """
        """

        today = datetime.today()
        
        try:
            path = Path(self.folder, "new_log", self.station)
            os.makedirs(path)
        except OSError:
            pass
        try:
            with open( Path(path, "response_log.csv"), mode="a", encoding="utf-8", newline='') as response_log:
                csv_write = csv.writer(response_log, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_write.writerow([f"Time: {today.strftime('%Y%m%d%H%M%S%f')[:-3]}", f"URL: {server_address}", f"CT: {json.loads(json_data)['CTMETHOD']}",
                                    {f"Status Code: {response.status_code}"}, f"Message: {response.text}"])
        except:
            pass

    def save_json_file(self, json_data):
        """
        Writes the log file to the file system.

        Usage:

        >>> # Calling the method:
        >>> self.log.save_json_file()
        """

        try:
            if self.folder:
                path = Path(self.folder, "new_log")
                os.makedirs(path)
            else:
                path = Path("/tmp/Log") if sys.platform.lower() == "linux" else Path("Log")
                os.makedirs(path)
        except OSError:
            pass

        log_file = f"{self.user}_{uuid.uuid4().hex}.json"

        if self.config.smart_test:
            self.log_exec_file()

        try:
            with open( Path(path, log_file), mode="w", encoding="utf-8") as json_file:
                json_file.write(json_data)
            logger().debug(f"Log file created successfully: {Path(path, log_file)}")
        except Exception as error:
            logger().debug(f"Fail in create json file in: {Path(path, log_file)}: Error: {str(error)}")
            pass

    def generate_log(self):
        """
        Generates a log entry with the execution details and sends it to the API.
        This method collects various details such as execution time, user, station, program, and results,
        and formats them into a dictionary that is then sent as a JSON payload to the specified API endpoint.

        """

        self.checks_empty_line()

        row = self.table_rows[1]
        total_cts = row[5]
        passed = row[6]
        failed = row[7]
        seconds = row[8]
        printable_message = row[11]
        sequence = uuid.uuid4().hex[:6]
        area = self.config.num_exec or "Desenvolvimento"
        minutes = float(seconds) / 60 if isinstance(seconds, (int, float)) else 0

        self.program = self.program or row[3]
        self.release = self.release or row[10]
        self.country = self.country or row[15]
        self.database = self.database or row[12]

        log_data = {
            "cLogDtExec": self.suite_datetime,
            "cLogNomUsr": self.user,
            "cLogNomEst": self.station,
            "cLogProgra": self.program,
            "cLogDtProg": "",
            "cLogHrProg": "",
            "nLogCtsOk": passed,
            "nLogCtsNok": failed,
            "nLogCtsSeg": seconds,
            "cLogVersao": self.version,
            "cLogReleas": self.release,
            "nLogCtsErr": printable_message,
            "cLogBancod": self.database,
            "cLogIdenti": self.issue,
            "cLogIdExec": self.execution_id,
            "cLogPais": self.country,
            "cLogTool": self.test_type,
            "cLogSequen": sequence,
            "nLogCtsTot": total_cts,
            "cLogDtExea": self.suite_datetime.split(" ")[0],
            "cLogHrExea": self.suite_datetime.split(" ")[1],
            "cLogArea": area,
            "cLogMnExec": minutes
        }

        api_url = self.config.api_url
        api_url_ip = self.config.api_url_ip
        path_folder = self.config.api_json_path
        
        self.table_rows.pop() # Remove the last row which is empty
        self.testcase_generate_log.append(self.get_testcase_stack())

        logger().debug(f'Json log_data: {log_data}')

        self.send_log_with_retries(log_data, api_url, api_url_ip, path_folder)

    def send_log_with_retries(self, log_data, api_url, api_url_ip, path_folder):
        headers = {"Content-Type": "application/json; charset=utf-8"}
        body = json.dumps(log_data)
        timeout_dns = 600
        timeout_ip = 1200
        max_retries = 4

        if not api_url or not api_url_ip:
            logger().info("Saving log locally.")
            self.save_log_locally(path_folder, body)
            return

        for attempt in range(1, max_retries + 1):
            try:
                # Primeiras tentativas usando DNS
                if attempt <= 2:
                    response = requests.post(f"{api_url}/createlog/", data=body, headers=headers, timeout=timeout_dns)
                # Tentativas adicionais usando IP
                else:
                    response = requests.post(f"{api_url_ip}/createlog/", data=body, headers=headers, timeout=timeout_ip)

                if response.status_code == 200:
                    logger().debug(f"[FwSendLog]: Log enviado com sucesso na tentativa {attempt}.")
                    return
                elif response.status_code == 400:
                    logger().debug("[FwSendLog]: Erro 400 - Limpando caracteres especiais do JSON.")
                    body = body.encode("ascii", "ignore").decode()

            except requests.RequestException as e:
                logger().debug(f"[FwSendLog]: Erro ao enviar log na tentativa {attempt}: {e}")

            time.sleep(3)  # Aguarda 3 segundos antes da próxima tentativa

        # Caso todas as tentativas falhem
        self.save_log_locally(path_folder, body)

    def save_log_locally(self, path_folder, body):
        """
        Saves the log data locally as a JSON file.
        """
        
        logger().info("[FwSendLog]: Não foi possível enviar o log após todas as tentativas.")
        log_file_name = f"{int(time.time())}.json"
        log_file_path = Path(path_folder, log_file_name)
        
        try:
            with open(log_file_path, "w", encoding="utf-8") as log_file:
                log_file.write(body)
                logger().info(f"[FwSendLog]: Log salvo localmente em {log_file_path}.")
        except IOError as e:
            logger().info(f"[FwSendLog]: Falha ao salvar o log localmente: {e}")

    def ident_test(self):
        """

        :return:
        """
        ct_method = self.get_testcase_stack()
        ct_number = ''.join(list(filter(str.isdigit, f"{ct_method.split('_')[-1]}"))) if ct_method else ""

        return (ct_method, ct_number)

    def take_screenshot_log(self, driver, description="", stack_item="", test_number=""):
        """
        [Internal]

        Takes a screenshot and saves on the log screenshot folder defined in config.

        :param driver: The selenium driver.
        :type: Selenium Driver
        :param stack_item: test case stack
        :type: str
        :param test_number: test case number
        :type: str

        Usage:

        >>> # Calling the method:
        >>> self.log.take_screenshot_log()
        """

        if not stack_item:
            stack_item = self.get_testcase_stack()

        if stack_item == "setUpClass":
            stack_item = f'{self.get_testcase_stack()}_{self.get_file_name("testsuite")}'

        if not test_number:
            test_number = f"{stack_item.split('_')[-1]} -" if stack_item else ""

        if not self.release:
            self.release = self.config.release

        testsuite = self.get_file_name("testsuite")

        today = datetime.today()

        if self.search_stack("log_error") and not description:
            screenshot_file = self.screenshot_file_name("error", stack_item)
        elif self.search_stack("CheckResult"):
            screenshot_file = self.screenshot_file_name("CheckResult", stack_item)
        else:
            screenshot_file = self.screenshot_file_name(description=description, stack_item=stack_item)

        if self.config.debug_log:
            logger().debug(f"take_screenshot_log in:{datetime.now()}\n")
            
        try:
            if self.config.log_http:
                folder_path = Path(self.config.log_http, self.config.country, self.release, self.config.issue, self.config.execution_id, testsuite)
                path = Path(folder_path, screenshot_file)
                os.makedirs(Path(folder_path))
            else:
                path = Path("/tmp/Log", self.station, screenshot_file) if sys.platform.lower() == "linux" else Path("Log", self.station, screenshot_file)
                os.makedirs(path)
        except OSError:
            pass

        try:
            driver.save_screenshot(str(path))
            logger().debug(f"Screenshot file created successfully: {path}")
        except Exception as e:
            logger().exception(f"Warning Log Error save_screenshot exception {str(e)}")

    def screenshot_file_name(self, description="", stack_item=""):
        """

        :param name:
        :return:
        """

        today = datetime.today()

        if description:
            return f"{self.user}_{today.strftime('%Y%m%d%H%M%S%f')[:-3]}_{stack_item}_{description}.png"
        else:
            return f"{self.user}_{today.strftime('%Y%m%d%H%M%S%f')[:-3]}_{stack_item}.png"

    def printable_message(self, string):
        """

        :param string:
        :return:
        """

        return re.sub(';', ',', ''.join(filter(lambda x: x.isprintable(), string))[:600])

    def search_stack(self, function):
        """
        Returns True if passed function is present in the call stack.

        :param function: Name of the function
        :type function: str

        :return: Boolean if passed function is present or not in the call stack.
        :rtype: bool

        Usage:

        >>> # Calling the method:
        >>> is_present = self.search_stack("MATA020")
        """
        return len(list(filter(lambda x: x.function == function, inspect.stack()))) > 0

    def get_program_name(self):
        """
        [Internal]
        """
        stack_item_splited = next(iter(map(lambda x: x.filename.split(self.replace_slash("\\")), filter(
            lambda x: "TESTSUITE.PY" in x.filename.upper() or "TESTCASE.PY" in x.filename.upper(), inspect.stack()))),
                                  None)

        if stack_item_splited:
            get_file_name = next(iter(list(
                map(lambda x: "TESTSUITE.PY" if "TESTSUITE.PY" in x.upper() else "TESTCASE.PY", stack_item_splited))))

            if get_file_name:
                program_name = next(iter(list(map(lambda x: re.findall(fr"(\w+)(?:{get_file_name})", x.upper()),
                                                  filter(lambda x: ".PY" in x.upper(), stack_item_splited)))), None)

                if program_name:
                    return next(iter(program_name))
                else:
                    return None
        else:
            return None

    def replace_slash(self, path):

        slash = r"/" if (sys.platform.lower() == "linux") else r"\\"

        pattern = re.compile(r'[\/\\]')

        if pattern.findall(path):
            return pattern.sub(slash, path)
