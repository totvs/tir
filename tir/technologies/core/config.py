import json

class ConfigLoader:
    '''
    This class is instantiated to contain all config information used throughout the execution of the methods.
    '''
    def __init__(self, path="config.json"):
        with open(path) as json_data_file:
            data = json.load(json_data_file)

        self.url = str(data["Url"])
        self.browser = str(data["Browser"])
        self.environment = str(data["Environment"])
        self.user = str(data["User"])
        self.password = str(data["Password"])
        self.language = str(data["Language"]) if "Language" in data else ""
        self.skip_environment = ("SkipEnvironment" in data and bool(data["SkipEnvironment"]))
        self.headless = ("Headless" in data and bool(data["Headless"]))
        self.log_folder = str(data["LogFolder"]) if "LogFolder" in data else ""
        self.log_file = ("LogFile" in data and bool(data["LogFile"]))
        self.valid_language = False
        self.initialprog = ""
        self.routine = ""
        self.date = ""
        self.group = ""
        self.branch = ""
        self.module = ""


        if self.language:
            self.valid_language = True
