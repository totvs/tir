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
        self.language = str(data["Language"])
        self.valid_language = False
        self.initialprog = ""
        self.date = ""
        self.group = ""
        self.branch = ""
        self.module = ""
        

        if self.language:
            self.valid_language = True
