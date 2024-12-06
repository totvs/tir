from tir.technologies.core.config import ConfigLoader
import requests
import json
import time
from tir.technologies.core.logging_config import logger
from pathlib import Path
import os


class NumExec():

    def __init__(self):
        self.config = ConfigLoader()

    def post_exec(self, url, numexec_folder):

        success_response = [200, 201]

        status = None

        endtime = time.time() + 120

        error = None

        strftime = time.strftime("%Y%m%d%H%M%S")

        while(time.time() < endtime and status not in success_response):

            try:
                status = self.send_request(url)
            except Exception as e:
                error = str(e)

            time.sleep(12)

        if error:
            response = str(f"STATUS: {status} Url: {url} ID: {self.config.num_exec} Error: {error}")
        else:
            response = str(f"STATUS: {status} Url: {url} ID: {self.config.num_exec}")

        logger().debug(response)
        if status not in success_response:

            try:
                path = Path(self.config.log_folder, numexec_folder)
                os.makedirs(path)
            except OSError:
                pass

            with open(Path(path, f"{self.config.num_exec}_TIR_{strftime}.txt"), "w") as json_log:
                json_log.write(response)

        return status in success_response

    def send_request(self, url):
        """

        :return json status response:
        """

        proxies = {
            "http": None,
            "https": None,
        }

        data = {'num_exec': self.config.num_exec, 'ip_exec': self.config.ipExec}

        response = requests.post(url.strip(), json=data, proxies=proxies)

        json_data = json.loads(response.text)

        return json_data["status"]