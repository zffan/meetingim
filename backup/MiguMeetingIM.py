import websocket
from util.settings import WS_LOG_NAME, HEART_BEAT_PERIOD
import logging
from web_server.webserver import WebAPI
from websocket import ABNF
logger = logging.getLogger(WS_LOG_NAME)
import json
from threading import Thread, Event
import time

class MiguMeetingIM(object):

    def __init__(self, url, roomId, userId):
        self.__url = url
        self.__roomId = roomId
        self.__userId = userId
        self.__stop = False
        self.__connected = False
        self.__msgId = 1
        login_resp = WebAPI.web_im_login(self.__userId, "123456")
        if login_resp['code'] == 0:
            authorization = login_resp['data']['authorization']
            enter_resp = WebAPI.web_meeting_enter(self.__roomId, '', authorization)
            if enter_resp['code'] == 0:
                self.__exp = enter_resp['data']['imExp']
                self.__ctime = enter_resp['data']['imCreateTime']
                self.__signature = enter_resp['data']['imSignature']

        self.__full_url = self.__url + "/im/ws?roomId=%s&userId=%s&exp=%s&ctime=%s&signature=%s" % (self.__roomId, self.__userId, self.__exp, self.__ctime, self.__signature)
        logger.debug("完整地址是:%s" % self.__full_url)
        logger.debug("加入会议室:%s" % self.__roomId)
        self.__socket_client = websocket.WebSocketApp(url=self.__full_url, on_open=self.on_open, on_close=self.on_close,
                                           on_message=self.on_message, on_error=self.on_error)

        self.locust_environment = None

    """
    解析接收大消息，根据消息类型，选择不同的处理方法
    """
    def parse_message(self, message):
        if "" == message:
            logger.debug("收到心跳回复！")
            if __name__ != "__main__":
                self.locust_environment.events.request_success.fire(request_type="WebSocket_connect", name='心跳回复',
                                                                    response_time=0,
                                                                    response_length=0)
            return
        else:
            recv_time = (int(round(time.time() * 1000)))
            msg_json = json.loads(message)
            msg_type = msg_json['type']
            send_time = int(msg_json['sendTime'])
            res_time = recv_time-send_time
            if msg_type == "0":
                logger.debug("收到消息:%s" % message)
                if __name__ != "__main__":
                    self.locust_environment.events.request_success.fire(request_type="WebSocket_recv", name='收到消息',
                                                                        response_time=res_time,
                                                                        response_length=0)
                msgId = msg_json['msgId']
                ack = {'type': 2, 'msgId': msgId, 'ack': 'msgAckOk'}
                logger.debug(ack)
                self.__socket_client.send(json.dumps(ack), ABNF.OPCODE_TEXT)
                msg = msg_json['data']
                if 'start_sendmsg' in msg:
                    msg_body = {"type": "0", "data": ["fzf_perftest "], "msgId": self.__msgId}
                    self.__msgId = self.__msgId + 1
                    self.__socket_client.send(json.dumps(msg_body), ABNF.OPCODE_TEXT)
                    logger.debug("发送消息%s" % msg_body)
                    if __name__ != "__main__":
                        self.locust_environment.events.request_success.fire(request_type="WebSocket_connect", name='发送消息',
                                                                            response_time=0,
                                                                            response_length=0)


    """
    启动
    """
    def run(self):
        logger.debug("启动会议IM连接")
        while True:
            if self.__stop:
                break
            if not self.__connected:
                self.__socket_client.run_forever()


    def stop(self):
        if 'Connected' in self.__socket_client.ConnectionStatus:
            self.__socket_client.Disconnect()
        self.__stop = True

    def reconnect(self, reason=None):
        if __name__ != "__main__":
            self.locust_environment.events.request_failure.fire(request_type="WebSocket_Send", name='重新连接',
                                                                response_time=0,
                                                                response_length=0, exception=reason)
        self.run()

    def on_open(self, state):
        logger.debug("开启连接！！")
        if __name__ != "__main__":
            self.locust_environment.events.request_success.fire(request_type="WebSocket_connect", name='启动IM连接',
                                                                response_time=0,
                                                                response_length=0)
        logger.debug("on_open")
        class HeartbeatThread(Thread):
            def __init__(self, event, ws, locust_environment):
                super(HeartbeatThread, self).__init__()
                self.event = event
                self.ws = ws
                self.locust_environment = locust_environment

            def run(self):
                while True:
                    self.ws.send("", ABNF.OPCODE_TEXT)
                    logger.debug("发送心跳！")
                    if __name__ != "__main__":
                        self.locust_environment.events.request_success.fire(request_type="WebSocket_Send", name='发送心跳',
                                                                        response_time=0,
                                                                        response_length=0)
                    self.event.wait(timeout=HEART_BEAT_PERIOD)

        event = Event()
        heartbeat = HeartbeatThread(event, self.__socket_client, self.locust_environment)
        heartbeat.start()

    def stop(self):
        self.__stop = True
        if 'Connected' in self.__socket_client.ConnectionStatus:
            self.__socket_client.Disconnect()
        if __name__ != "__main__":
            self.locust_environment.events.request_success.fire(request_type="WebSocket_connect", name='停止IM连接',
                                                                response_time=0,
                                                                response_length=0)

    def on_message(self, _, message):
        self.parse_message(message)



    def on_close(self,_, code, close_msg):
        logger.debug("On_Close")
        if __name__ != "__main__":
            self.locust_environment.events.request_failure.fire(request_type="WebSocket_Send", name='关闭连接',
                                                                response_time=0,
                                                                response_length=0, exception=close_msg)

    def on_error(self, _, error):
        logger.debug("On_Error:%s" % error)
        if __name__ != "__main__":
            self.locust_environment.events.request_failure.fire(request_type="WebSocket_Send", name='异常断开连接',
                                                                response_time=0,
                                                                response_length=0, exception=error)


if __name__ == "__main__":
    client = MiguMeetingIM('wss://meeting-test.migu.cn:7778', "635986937", "19900009998")
    client.run()