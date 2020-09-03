from tir.technologies.core.config import ConfigLoader
import requests
import json
import time

class NumExec(ConfigLoader):

    def __init__(self):
        super().__init__()

    def post_exec(self, url):

        success_response = [200, 201]

        status = None

        endtime = time.time() + 120

        error = None

        id_error = time.strftime("%Y%m%d%H%M%S")

        while(time.time() < endtime and status not in success_response):

            try:
                status = self.send_request(url)
            except Exception as e:
                error = str(e)

            time.sleep(12)

        response = str(f"STATUS: {status} Url: {url} ID: {id_error} Error: {error}")
        print(response)
        if status not in success_response:
            with open(f"{self.log_folder}\{id_error}_json_data_response.txt", "w") as json_log:
                json_log.write(response)

        return status in success_response

    def send_request(self, url):
        """

        :return json status response:
        """

        data = {'num_exec': self.num_exec, 'ip_exec': self.ipExec}

        response = requests.post(url.strip(), json=data)

        json_data = json.loads(response.text)

        return json_data["status"]