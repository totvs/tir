import json
import os

class ConfigLoader:
    """
    This class is instantiated to contain all config information used throughout the execution of the methods.
    """
    def __init__(self, path="config.json"):
        valid = os.path.isfile(path)

        if valid:
            with open(path) as json_data_file:
                data = json.load(json_data_file)
        else:
            data = {}

        self.autostart = True
        self.ipExec = str(data["ipExec"]) if "ipExec" in data else ""
        self.url_set_start_exec = str(data["UrlSetStartExec"]) if "UrlSetStartExec" in data else ""
        self.url_set_end_exec = str(data["UrlSetEndExec"]) if "UrlSetEndExec" in data else ""
        self.screenshot = bool(data["ScreenShot"]) if "ScreenShot" in data else True
        self.country = str(data["Country"]) if "Country" in data else "BRA"
        self.execution_id = str(data["ExecId"]) if "ExecId" in data else ""
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
        self.valid_language = self.language != ""
        self.initial_program = ""
        self.routine = ""
        self.date = ""
        self.group = ""
        self.branch = ""
        self.module = ""
