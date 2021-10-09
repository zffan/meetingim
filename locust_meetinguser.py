from locust import User, between
import queue
from backup.AsyncMeetingIM import AsyncMeetingIM
from util.settings import WS_LOG_NAME
import logging
logger = logging.getLogger(WS_LOG_NAME)
# roomId = ["343055800", "883038883", "695730144", "342172707", "346780065"]
roomId = ["205078400"]

"""
准备测试数据，每个进程1000个用户
"""
queue_data = queue.Queue()
for imuser in range(19900005001, 19900005501):
    index = imuser % len(roomId)
    userdata = (imuser, roomId[index])
    queue_data.put_nowait(userdata)


class AmberPushUser(User):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从消息队列中获取登录的用户
        user = queue_data.get()
        logger.debug("roomId:%s, userid: %s" % (user[1], user[0]))
        self.client = AsyncMeetingIM(self.host, user[1], user[0], self.environment)



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
