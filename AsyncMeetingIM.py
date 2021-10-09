import json
import time
import logging
from json import JSONDecodeError
from meetingwebsocketapp import MeetingWebSocketApp
from util.settings import WS_LOG_NAME, HEART_BEAT_PERIOD
from web_server.webserver import WebAPI
from websocket import ABNF

logger = logging.getLogger(WS_LOG_NAME)

"""
继承WebSocketApp，重新处理心跳逻辑
"""

class AsyncMeetingIM(object):

    def __init__(self, url, roomId, userId, locust_environment=None, passwd='123456'):
        self.__url = url
        self.__roomId = roomId
        self.__userId = userId
        self.__msgId = 1
        self.locust_environment = locust_environment
        self.__socket_client = None
        exp, ctime, signature = self._join_meeting_room(userId, passwd, roomId)
        self._parse_functions = {
            "0": self._parse_im, "2": self._parse_heartbeat, "3": self._parse_subtitle
        }

        if exp:
            self.__full_url = self.__url + "/im/ws?roomId=%s&userId=%s&exp=%s&ctime=%s&signature=%s" % (
                roomId, userId, exp, ctime, signature)
            logger.info("会议室完整地址是:%s" % self.__full_url)
            logger.info("用户：%s加入会议室:%s" % (self.__userId, self.__roomId))
            self.__socket_client = MeetingWebSocketApp(url=self.__full_url, on_open=self.on_open, on_close=self.on_close,
                                                       on_message=self.on_message, on_error=self.on_error,
                                                       on_pong=self.on_pong, on_ping=self.on_ping, OPCODE_TEXT_PING=True)
        else:
            if __name__ != "__main__":
                self.locust_environment.events.request_failure.fire(request_type="HTTP", name='加入会议',
                                                                    response_time=0,
                                                                    response_length=0,exception=f"exp:{exp}, ctime{ctime}, signature{signature}")


    """
    启动
    """

    def run(self):
        if self.__socket_client:
            self.__socket_client.run_forever(ping_payload="", ping_interval=HEART_BEAT_PERIOD)


    def on_open(self, state):
        logger.debug("开启连接......")
        if __name__ != "__main__":
            self.locust_environment.events.request_success.fire(request_type="WebSocket", name='on_open',
                                                                response_time=0,
                                                                response_length=0)

    def on_message(self, _, message):
        logger.debug(message)
        try:
            recv_time = (int(round(time.time() * 1000)))
            msg_json = json.loads(message)
            msg_type = msg_json['type']
            callback = self._parse_functions.get(msg_type)
            logger.debug(callback)
            callback(msg_json, recv_time)
        except JSONDecodeError:
            if __name__ != "__main__":
                self.locust_environment.events.request_failure.fire(request_type="WebSocket", name='收到异常请求报文',
                                                                    response_time=0,
                                                                    response_length=0,
                                                                    exception=message)
        except KeyError:
            logger.debug("keyerror")
            if __name__ != "__main__":
                self.locust_environment.events.request_failure.fire(request_type="WebSocket", name='收到异常请求报文',
                                                                    response_time=0,
                                                                    response_length=0,
                                                                    exception=message)

    def on_pong(self, _, message):
        logger.debug("one_pong:%s" % message)

    def on_ping(self, _, message):
        logger.debug("one_pong:%s" % message)

    def on_close(self, _, *args):
        logger.debug(f"on_close:{args}")
        if __name__ != "__main__":
            self.locust_environment.events.request_failure.fire(request_type="WebSocket", name='on_close',
                                                                response_time=0,
                                                                response_length=0,
                                                                exception=args)

    def on_error(self, _, error):
        logger.debug("On_Error:%s" % error)
        if __name__ != "__main__":
            self.locust_environment.events.request_failure.fire(request_type="WebSocket", name='on_error',
                                                                response_time=0,
                                                                response_length=0, exception=error)

    """
    加入会议，获取会议信息
    """

    def _join_meeting_room(self, userid, passwd, roomId):
        authorization = WebAPI.web_im_login(userid, passwd)
        imExp, imCreateTime, imSignature = WebAPI.web_meeting_enter(roomId, '', authorization)
        return imExp, imCreateTime, imSignature

    """
    
    """
    def _parse_heartbeat(self, message, resp_time):
        logger.debug("收到心跳回复！")
        if __name__ != "__main__":
            self.locust_environment.events.request_success.fire(request_type="WebSocket", name='心跳回复',
                                                                response_time=0,
                                                                response_length=0)

    def _parse_im(self, message, recv_time):
        logger.debug("收到消息:%s" % message)

        try:
            send_time = int(message['sendTime'])
            res_time = recv_time - send_time
            if __name__ != "__main__":
                self.locust_environment.events.request_success.fire(request_type="WebSocket", name='收到消息',
                                                                    response_time=res_time,
                                                                    response_length=0)
            msgId = message['msgId']
            ack = {'type': 2, 'msgId': msgId, 'ack': 'msgAckOk'}
            logger.debug("回复消息确认：%s" % ack)
            self.__socket_client.send(json.dumps(ack), ABNF.OPCODE_TEXT)
            msg = message['data']
            if 'start_sendmsg' in msg:
                msg_body = {"type": "0", "data": ["fzf_perftest "], "msgId": self.__msgId}
                self.__msgId = self.__msgId + 1
                self.__socket_client.send(json.dumps(msg_body), ABNF.OPCODE_TEXT)
                logger.debug("发送消息%s" % msg_body)
                if __name__ != "__main__":
                    self.locust_environment.events.request_success.fire(request_type="WebSocket",
                                                                        name='发送消息',
                                                                        response_time=0,
                                                                        response_length=0)
        except JSONDecodeError:
            if __name__ != "__main__":
                self.locust_environment.events.request_failure.fire(request_type="WebSocket", name='收到异常请求报文',
                                                                            response_time=0,
                                                                            response_length=0,
                                                                            exception=message)
        except KeyError:
            if __name__ != "__main__":
                self.locust_environment.events.request_failure.fire(request_type="WebSocket", name='收到异常请求报文',
                                                                        response_time=0,
                                                                        response_length=0,
                                                                        exception=message)

    def _parse_subtitle(self, message, recv_time):
        try:
            msg = message['data']
            if len(msg) >= 1:
                for i in range(len(msg)):
                    send_time = json.loads(msg[i])['senderTime']
                    res_time = recv_time - send_time
                    if __name__ != "__main__":
                        self.locust_environment.events.request_success.fire(request_type="WebSocket",
                                                                            name=f'会议室：{self.__roomId}收到字幕',
                                                                            response_time=res_time, response_length=0)

        except JSONDecodeError:
            logger.debug("JSONDecodeError")
            if __name__ != "__main__":
                self.locust_environment.events.request_failure.fire(request_type="WebSocket", name='收到异常请求报文',
                                                                    response_time=0,
                                                                    response_length=0,
                                                                    exception=message)
        except KeyError:
            logger.debug("KeyError")
            if __name__ != "__main__":
                self.locust_environment.events.request_failure.fire(request_type="WebSocket", name='收到异常请求报文',
                                                                    response_time=0,
                                                                    response_length=0,
                                                                    exception=message)


if __name__ == "__main__":
    # client = AsyncMeetingIM('wss://meeting-dev.migu.cn:7778', "205078400", "19900005001")
    client = AsyncMeetingIM('wss://meeting-dev.migu.cn:7778', "244169934", "19900005001")
    client.run()
