import json
import os
from datetime import datetime
import sys

class ConfigLoader:
    """
    This class is instantiated to contain all config information used throughout the execution of the methods.
    """

    _instance = None
    _json_data = None

    def __new__(cls, path="config.json"):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._initialize(path)
        return cls._instance

    def _initialize(self, path="config.json"):
        if ConfigLoader._json_data is None:
            if not path:
                path = os.path.join(sys.path[0], r"config.json")

            if not os.path.isfile(path):
                raise FileNotFoundError(f"Arquivo de configuração não encontrado: {path}")

            try:
                with open(path, 'r', encoding='utf-8') as json_data_file:
                    data = json.load(json_data_file)

                    bypass_check_keys = data.get('SmartTest', False)
                    key_validation_result = None  # Initialize to a default value

                    if not bypass_check_keys:
                        key_validation_result = self.check_keys(data)

                    if key_validation_result:
                        raise ValueError(f"Configuration validation error: {key_validation_result}")

                    ConfigLoader._json_data = data

            except json.JSONDecodeError as e:
                raise ValueError(f"Error parsing JSON file '{path}': {e}. Please check the JSON syntax.")
            except Exception as e:
                raise RuntimeError(f"Unexpected problem loading configuration file: {e}. \n* Please check your config.json *")

        if ConfigLoader._json_data:
            for key, value in ConfigLoader._json_data.items():
                setattr(self, key, value)

            data = ConfigLoader._json_data

            today = datetime.today()
            self.json_data = data
            self.autostart = True
            self.ipExec = str(data["ipExec"]) if "ipExec" in data else ""
            self.url_set_start_exec = str(data["UrlSetStartExec"]) if "UrlSetStartExec" in data else ""
            self.url_set_end_exec = str(data["UrlSetEndExec"]) if "UrlSetEndExec" in data else ""
            self.screenshot = bool(data["ScreenShot"]) if "ScreenShot" in data else True
            self.country = str(data["Country"]) if "Country" in data else "BRA"
            self.execution_id = str(data["ExecId"]) if "ExecId" in data else today.strftime('%Y%m%d')
            self.num_exec = str(data["NumExec"]) if "NumExec" in data else ""
            self.issue = str(data["MotExec"]) if "MotExec" in data else ""
            self.url = str(data["Url"]) if "Url" in data else ""
            self.browser = str(data["Browser"]) if "Browser" in data else ""
            self.environment = str(data["Environment"])  if "Environment" in data else ""
            self.user = str(data["User"]) if "User" in data else ""
            self.password = str(data["Password"]) if "Password" in data else ""
            self.language = str(data["Language"]) if "Language" in data else ""
            self.skip_environment = ("SkipEnvironment" in data and bool(data["SkipEnvironment"]))
            self.headless = ("Headless" in data and bool(data["Headless"]))
            self.log_folder = str(data["LogFolder"]) if "LogFolder" in data else ""
            self.log_file = ("LogFile" in data and bool(data["LogFile"]))
            self.debug_log = ("DebugLog" in data and bool(data["DebugLog"]))
            self.time_out = int(data["TimeOut"]) if "TimeOut" in data else 90
            self.parameter_menu = str(data["ParameterMenu"]) if "ParameterMenu" in data else ""
            self.screenshot_folder = str(data["ScreenshotFolder"]) if "ScreenshotFolder" in data else ""
            self.coverage = ("Coverage" in data  and bool(data["Coverage"]))
            self.skip_restart = ("SkipRestart" in data and bool(data["SkipRestart"]))
            self.smart_test = ("SmartTest" in data and bool(data["SmartTest"]))
            self.smart_erp = ("SmartERP" in data and bool(data["SmartERP"]))
            self.user_cfg = str(data["UserCfg"]) if "UserCfg" in data else ""
            self.password_cfg = str(data["PasswordCfg"]) if "PasswordCfg" in data else ""
            self.electron_binary_path = (str(data["BinPath"]) if "BinPath" in data else "")
            self.csv_path = (str(data["CSVPath"]) if "CSVPath" in data else "")
            self.database_driver = str(data["DBDriver"]) if "DBDriver" in data else ""
            self.database_server = str(data["DBServer"]) if "DBServer" in data else ""
            self.database_port = str(data["DBPort"]) if "DBPort" in data else ""
            self.database_name = str(data["DBName"]) if "DBName" in data else ""
            self.database_user = str(data["DBUser"]) if "DBUser" in data else ""
            self.database_password = str(data["DBPassword"]) if "DBPassword" in data else ""
            self.dbq_oracle_server = str(data["DBQOracleServer"]) if "DBQOracleServer" in data else ""
            self.url_tss = str(data["URL_TSS"]) if "URL_TSS" in data else ""
            self.start_program = str(data["StartProgram"]) if "StartProgram" in data else ""
            self.new_log = ("NewLog" in data  and bool(data["NewLog"]))
            self.logurl1 = str(data["LogUrl1"]) if "LogUrl1" in data else ""
            self.logurl2 = str(data["LogUrl2"]) if "LogUrl2" in data else ""
            self.parameter_url = bool(data["ParameterUrl"]) if "ParameterUrl" in data else False
            self.log_http = str(data["LogHttp"]) if "LogHttp" in data else ""
            self.baseline_spool = str(data["BaseLine_Spool"]) if "BaseLine_Spool" in data else ""
            self.check_value = (bool(data["CheckValue"]) if "CheckValue" in data else None)
            self.poui_login = bool(data["POUILogin"]) if "POUILogin" in data else False
            self.poui = bool(data["POUI"]) if "POUI" in data else False
            self.log_info_config = bool(data["LogInfoConfig"]) if "LogInfoConfig" in data else False
            self.release = str(data["Release"]) if "Release" in data else "12.1.2210"
            self.top_database = str(data["TopDataBase"]) if "TopDataBase" in data else "MSSQL"
            self.lib_version = str(data["Lib"]) if "Lib" in data else "lib_version"
            self.build_version = str(data["Build"]) if "Build" in data else "build_version"
            self.appserver_folder = str(data["AppServerFolder"]) if "AppServerFolder" in data else ""
            self.destination_folder = str(data["DestinationFolder"]) if "DestinationFolder" in data else ""
            self.appserver_service = str(data["AppServerService"]) if "AppServerService" in data else ""
            self.check_dump = ("CheckDump" in data and bool(data["CheckDump"]))
            self.chromedriver_auto_install = ("ChromeDriverAutoInstall" in data and bool(data["ChromeDriverAutoInstall"]))
            self.ssl_chrome_auto_install_disable = (
                        "SSLChromeInstallDisable" in data and bool(data["SSLChromeInstallDisable"]))
            self.data_delimiter = str(data["DataDelimiter"]) if "DataDelimiter" in data else "/"
            self.procedure_menu = str(data["ProcedureMenu"]) if "ProcedureMenu" in data else ""
            self.valid_language = self.language != ""
            self.initial_program = ""
            self.routine = ""
            self.date = ""
            self.group = ""
            self.branch = ""
            self.module = ""
            self.routine_type = ""
            self.api_url = str(data["APIURL"]) if "APIURL" in data else ""
            self.api_url_ip = str(data["APIURLIP"]) if "APIURLIP" in data else ""
            self.api_json_path = str(data["APIJSONPATH"]) if "APIJSONPATH" in data else os.path.join(os.getcwd())
            self.server_mock  = str(data["ServerMock"]) if "ServerMock" in data else ""
            self.sso_login = ("SSOLogin" in data and bool(data["SSOLogin"]))


    def check_keys(self, json_data):
        valid_keys = [
        "ipExec",
        "UrlSetStartExec",
        "UrlSetEndExec",
        "ScreenShot",
        "Country",
        "ExecId",
        "NumExec",
        "MotExec",
        "Url",
        "Browser",
        "Environment",
        "User",
        "Password",
        "Language",
        "SkipEnvironment",
        "Headless",
        "LogFolder",
        "LogFile",
        "DebugLog",
        "TimeOut",
        "ParameterMenu",
        "ScreenshotFolder",
        "Coverage",
        "SkipRestart",
        "SmartTest",
        "SmartERP",
        "UserCfg",
        "PasswordCfg",
        "BinPath",
        "CSVPath",
        "DBDriver",
        "DBServer",
        "DBPort",
        "DBName",
        "DBUser",
        "DBPassword",
        "DBQOracleServer",
        "URL_TSS",
        "StartProgram",
        "NewLog",
        "LogUrl1",
        "LogUrl2",
        "ParameterUrl",
        "LogHttp",
        "BaseLine_Spool",
        "CheckValue",
        "POUILogin",
        "POUI",
        "LogInfoConfig",
        "Release",
        "TopDataBase",
        "Lib",
        "Build",
        "AppServerFolder",
        "DestinationFolder",
        "AppServerService",
        "CheckDump",
        "ChromeDriverAutoInstall",
        "SSLChromeInstallDisable",
        "DataDelimiter",
        "ProcedureMenu",
        "APIURL",
        "APIURLIP",
        "APIJSONPATH",
        "ServerMock",
        "SSOLogin"
    ]
        keys_json = set(json_data.keys())
        wrong_keys = keys_json - set(valid_keys)

        if wrong_keys:
            return str(f"The following keys are not expected or are incorrect on config.json: {wrong_keys}. Please Check! https://totvs.github.io/tir/configjson.html")

