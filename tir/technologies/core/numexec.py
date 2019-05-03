from tir.technologies.core.config import ConfigLoader
import requests

class NumExec:

    def __init__(self):

        self.config = ConfigLoader()

    def post_exec(self, url):

            data = {'num_exec': self.config.num_exec,'ip_exec': self.config.ipExec}

            return requests.post(url.strip(), json=data)