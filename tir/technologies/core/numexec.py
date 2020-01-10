from tir.technologies.core.config import ConfigLoader
import requests
import json
import time

class NumExec:

    def __init__(self):

        self.config = ConfigLoader()

    def post_exec(self, url):

        status = None

        endtime = time.time() + 120

        while(time.time() < endtime and status != 200):

            data = {'num_exec': self.config.num_exec,'ip_exec': self.config.ipExec}

            response = requests.post(url.strip(), json=data)

            json_data = json.loads(response.text)

            status = json_data["status"]

            if status != 200:
                time.sleep(12)

        print(f"Num exec. status: {status} Url: {url}")
        if status != 200:
            with open(f"E:\\smart_test\\logs_tir\\{time.time()}_json_data_response.txt", "w") as json_log:
                json_log.write(str(f"STATUS: {status}"))