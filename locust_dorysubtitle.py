from locust import User, between
import queue
from MeetingSubtitle import MeetingSubtitle
from util.settings import WS_LOG_NAME
import logging
logger = logging.getLogger(WS_LOG_NAME)
roomIds = ["205078400"]

"""
准备测试数据，每个进程1000个用户
"""
queue_data = queue.Queue()
for roomId in roomIds:
    queue_data.put_nowait(roomId)


class DorySubTitleUser(User):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从消息队列中获取登录的用户
        user = queue_data.get()
        logger.debug("roomId:%s" % user)
        self.client = MeetingSubtitle(self.host, user)
        self.client.locust_environment = self.environment


    """
    vuser启动
    """
    def on_start(self):
        self.client.run()

    """
    vuser停止
    """
    def on_stop(self):
        pass

    def sendmsg(self):
        pass

    tasks = [sendmsg]
    wait_time = between(0, 0)
