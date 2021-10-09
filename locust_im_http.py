import time
from locust import HttpUser, task, between, constant
from locust.contrib.fasthttp import FastHttpUser
from util.settings import WEB_URL, WS_LOG_NAME, WEB_HEADERS_DEFAULT
import logging
import json
from json import JSONDecodeError
import queue

logger = logging.getLogger(WS_LOG_NAME)

roomId = ["542349387"]

"""
准备测试数据，每个进程1000个用户
"""
queue_data = queue.Queue()
for imuser in range(19900006001, 19900006501):
    index = imuser % len(roomId)
    userdata = (imuser, roomId[index])
    queue_data.put_nowait(userdata)


class Meeting_im_http(FastHttpUser):
    wait_time = constant(0)

    @task
    def login_enter(self):
        user = queue_data.get()
        data = {'phoneNumber': user[0], 'dynamicCode': '123456', "from": 1}
        queue_data.put_nowait(user)
        with self.client.post("/sy/login/sms", data=json.dumps(data), headers=WEB_HEADERS_DEFAULT,
                              catch_response=True) as response:
            # logger.debug(response.text)
            try:
                if response.json()["code"] == 0:
                    authorization = response.json()["data"]["authorization"]
                else:
                    response.failure("Code is not 0")

            except JSONDecodeError:
                response.failure("Response could not be decoded as JSON")
            except KeyError:
                response.failure(f"Response did not contain expected key 'authorization'{response.text}")

        header = {"Authorization": authorization}
        WEB_HEADERS_DEFAULT.update(header)
        data_enter = {'roomId': user[1], 'password': "123456", "enterType": "ID入会"}

        with self.client.post("/sy/meeting/room/enter", data=json.dumps(data_enter), headers=WEB_HEADERS_DEFAULT,
                              catch_response=True) as response:
            try:
                if response.json()["code"] != 0:
                    response.failure(f"Code is not 0：{response.text}")
            except JSONDecodeError:
                response.failure("Response could not be decoded as JSON")
            except KeyError:
                response.failure(f"Response did not contain expected key 'code'：{response.text}")

