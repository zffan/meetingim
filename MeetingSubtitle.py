import json
import time
import logging
from websocket import WebSocketApp
from util.settings import WS_LOG_NAME, DORY_SUBTILE_PERIOD,APPSECRET,APPID
from web_server.webserver import WebAPI
from websocket import ABNF
from util.string_utils import StringUtils
import threading


logger = logging.getLogger(WS_LOG_NAME)

"""
继承WebSocketApp，重新处理心跳逻辑
"""


class MeetingWebSocketApp(WebSocketApp):

    def __init__(self, url, header=None,
                 on_open=None, on_message=None, on_error=None,
                 on_close=None, on_ping=None, on_pong=None,
                 on_cont_message=None,
                 keep_running=True, get_mask_key=None, cookie=None,
                 subprotocols=None,
                 on_data=None, OPCODE_TEXT_PING=False):

        super().__init__(url, header,
                         on_open, on_message, on_error,
                         on_close, on_ping, on_pong,
                         on_cont_message,
                         keep_running, get_mask_key, cookie,
                         subprotocols,
                         on_data)
        self.locust_environment = None
        self.OPCODE_TEXT_PING = OPCODE_TEXT_PING

    def _send_ping(self, interval, event, payload):
        while not event.wait(interval):
            self.last_ping_tm = time.time()
            if self.sock:
                try:
                    if self.OPCODE_TEXT_PING:
                        if isinstance(payload, dict):
                            payload['senderTime'] = int(round(time.time() * 1000))
                            self.sock.send(json.dumps(payload))
                            if __name__ != "__main__":
                                self.locust_environment.events.request_success.fire(request_type="WebSocket",
                                                                                    name='发送字幕',
                                                                                    response_time=0,
                                                                                    response_length=0)
                        else:
                            self.sock.send(payload)
                    else:
                        self.sock.ping(payload)
                except Exception as ex:
                    logger.warning("send_ping routine terminated: {}".format(ex))
                    break



class MeetingSubtitle(object):

    def __init__(self, url, roomid):
        self.__url = url
        self.__roomId = roomid
        currenttimestamp = int(round(time.time() * 1000))
        random = StringUtils.generate_random_str(8, True)
        sign_src = f'roomId={roomid}&applicationId={APPID}&currentTimeStamp={currenttimestamp}&random={random}'
        sign = StringUtils.get_sign(sign_src, APPSECRET)
        self.__full_url = self.__url + f'/im/subtitle?roomId={roomid}&currentTimeStamp={currenttimestamp}&random={random}&sign={sign}'
        logger.info("会议室完整地址是:%s" % self.__full_url)
        logger.info("加入会议室:%s" % roomid)
        self.__socket_client = MeetingWebSocketApp(url=self.__full_url, on_open=self.on_open, on_close=self.on_close,
                                                   on_message=self.on_message, on_error=self.on_error,
                                                   on_pong=self.on_pong, on_ping=self.on_ping, OPCODE_TEXT_PING=True)
        self.locust_environment = None


    """
    启动
    """

    def run(self):
        title = {
            "roomId": self.__roomId,
            "senderId": "19900000000",
            "senderName": "fanzhanfei",
            "language": "cn",
            "cnText": "性能测试-中文文本",
            "enText": "性能测试-英文文本",
            "senderTime": int(round(time.time() * 1000)),
            "resultType": "1"
        }
        self.__socket_client.locust_environment = self.locust_environment
        self.__socket_client.run_forever(ping_payload=title
                                         , ping_interval=DORY_SUBTILE_PERIOD)


    def on_open(self, state):
        logger.debug("开启连接......")
        if __name__ != "__main__":
            self.locust_environment.events.request_success.fire(request_type="WebSocket", name='on_open',
                                                                response_time=0,
                                                                response_length=0)

    def on_message(self, _, message):
        self._parse_message(message)

    def on_pong(self, _, message):
        logger.debug("one_pong:%s" % message)

    def on_ping(self, _, message):
        logger.debug("one_pong:%s" % message)

    def on_close(self, _, code, message):
        logger.debug("on_close:%s" % message)
        if __name__ != "__main__":
            self.locust_environment.events.request_failure.fire(request_type="WebSocket", name='on_close',
                                                                response_time=0,
                                                                response_length=0,
                                                                exception="code:%s, message: %s" % (code, message))

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
        login_resp = WebAPI.web_im_login(userid, passwd)
        if login_resp['code'] == 0:
            authorization = login_resp['data']['authorization']
            enter_resp = WebAPI.web_meeting_enter(roomId, '', authorization)
            if enter_resp['code'] == 0:
                exp = enter_resp['data']['imExp']
                ctime = enter_resp['data']['imCreateTime']
                signature = enter_resp['data']['imSignature']
        return exp, ctime, signature

    """
    解析接收大消息，根据消息类型，选择不同的处理方法
    """

    def _parse_message(self, message):
        if "" == message:
            logger.debug("收到心跳回复！")
            if __name__ != "__main__":
                self.locust_environment.events.request_success.fire(request_type="WebSocket", name='心跳回复',
                                                                    response_time=0,
                                                                    response_length=0)
            return
        else:
            recv_time = (int(round(time.time() * 1000)))
            msg_json = json.loads(message)
            msg_type = msg_json['type']
            send_time = int(msg_json['sendTime'])
            res_time = recv_time - send_time
            if msg_type == "0":
                logger.debug("收到消息:%s" % message)
                if __name__ != "__main__":
                    self.locust_environment.events.request_success.fire(request_type="WebSocket", name='收到消息',
                                                                        response_time=res_time,
                                                                        response_length=0)
                msgId = msg_json['msgId']
                ack = {'type': 2, 'msgId': msgId, 'ack': 'msgAckOk'}
                logger.debug("回复消息确认：%s" % ack)
                self.__socket_client.send(json.dumps(ack), ABNF.OPCODE_TEXT)
                msg = msg_json['data']
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

if __name__ == "__main__":
    client = MeetingSubtitle('wss://meeting-dev.migu.cn:7778', "205078400")
    client.run()