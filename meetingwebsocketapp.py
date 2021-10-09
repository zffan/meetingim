from websocket import WebSocketApp
import time
import logging
from util.settings import WS_LOG_NAME, HEART_BEAT_PERIOD
logger = logging.getLogger(WS_LOG_NAME)

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

        self.OPCODE_TEXT_PING = OPCODE_TEXT_PING

    def _send_ping(self, interval, event, payload):
        while not event.wait(interval):
            self.last_ping_tm = time.time()
            if self.sock:
                try:
                    if self.OPCODE_TEXT_PING:
                        self.sock.send(payload)
                    else:
                        self.sock.ping(payload)
                except Exception as ex:
                    logger.warning("send_ping routine terminated: {}".format(ex))
                    break