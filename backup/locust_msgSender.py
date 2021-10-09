from locust import User, between
import queue
from backup.MiguMeetingSendMSG import MiguMeetingSendMSG
from util.settings import WS_LOG_NAME
import logging
logger = logging.getLogger(WS_LOG_NAME)
roomId = ["329576638", "329576638", "329576638", "329576638", "329576638"]

"""
准备测试数据，每个进程1000个用户
"""
queue_data = queue.Queue()
for imuser in range(19900009001, 19900009006):
    index = imuser % 5
    userdata = (imuser, roomId[index])
    queue_data.put_nowait(userdata)


class AmberPushUser(User):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从消息队列中获取登录的用户
        user = queue_data.get()
        logger.debug("roomId:%s, userid: %s" % (user[1], user[0]))
        self.client = MiguMeetingSendMSG(self.host, user[1], user[0])
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
        self.client.stop()

    def sendmsg(self):
        pass

    tasks = [sendmsg]
    wait_time = between(0, 0)
