import requests
import json
from util.settings import WEB_URL, WS_LOG_NAME, WEB_HEADERS_DEFAULT
import logging
from json import JSONDecodeError
import time

logger = logging.getLogger(WS_LOG_NAME)


class WebAPI(object):

    @staticmethod
    def web_im_login(phoneNumber, dynamicCode):
        data = {'phoneNumber': phoneNumber, 'dynamicCode': dynamicCode, "from": 1}
        repeat_time = 3
        index = 0
        while index <= repeat_time:
            with requests.post(url=WEB_URL + '/sy/login/sms', headers=WEB_HEADERS_DEFAULT, data=json.dumps(data).encode('utf-8')) as response:
                try:
                    if response.status_code == 200:
                        res_text = response.json()
                        return res_text['data']['authorization']
                    else:
                        index = index + 1
                        time.sleep(3)
                        continue
                except JSONDecodeError:
                    index = index + 1
                    time.sleep(3)
                    continue
                except KeyError:
                    index = index + 1
                    time.sleep(3)
                    continue
        return None


    @staticmethod
    def web_meeting_enter(roomId, passwd, authorization):
        header = {"Authorization": authorization}
        WEB_HEADERS_DEFAULT.update(header)
        data = {'roomId': roomId, 'password': passwd, "enterType": "ID入会"}
        repeat_time = 3
        index = 0
        while index <= repeat_time:
            logger.debug(f"第{index}次加入")
            with requests.post(url=WEB_URL + '/sy/meeting/room/enter', headers=WEB_HEADERS_DEFAULT, data=json.dumps(data).encode('utf-8')) as response:
                try:
                    if response.status_code == 200:
                        res_text = response.json()
                        return res_text['data']['imExp'], res_text['data']['imCreateTime'], res_text['data']['imSignature']
                    else:
                        index = index + 1
                        time.sleep(3)
                        continue
                except JSONDecodeError:
                    index = index + 1
                    time.sleep(3)
                    continue
                except KeyError:
                    index = index + 1
                    time.sleep(3)
                    continue
        return None, None, None


if __name__ == "__main__":
    authorization = WebAPI.web_im_login("19900000000", "123456")
    data = WebAPI.web_meeting_enter('605245946', '', authorization)
    print(data)