# coding:utf-8
import configparser
import os
from pkg.logconfig import init_logging
from util.file_utils import File_utils
import json

# 初始化配置文件
config = configparser.ConfigParser()
ROOT = File_utils.project_root_path("meetingim")
print(ROOT)
CONF_FILE = os.path.join(ROOT, "conf", "server.conf")
config.read(CONF_FILE)


# global
GLOBAL_APP_KEY = config.get('global', 'app_key')
GLOBAL_AES_KEY = bytes(config.get('global', 'aes_key'), encoding='utf-8')

# logs
WS_LOG_NAME = config.get('logs', 'ws_log_name')

# tcp
TCP_HOST = config.get('tcp', 'host')

TCP_PORT = config.get('tcp', 'port')
HEART_BEAT_PERIOD = int(config.get('tcp', 'heart_beat_period'))
DORY_SUBTILE_PERIOD = float(config.get('tcp', 'dory_subtile_period'))

# Web Server公共参数
WEB_URL = config.get('web', 'web_url')
WEB_API_VERSION_DEFAULT = config.get('web', 'api_version_default')
WEB_TERMINAL_DEFAULT = config.get('web', 'terminal_dafault')
WEB_lOGIN_FLAG_DEFAULT= config.get('web', 'login_flag_default')
WEB_HEADERS_DEFAULT = json.loads(config.get('web', 'headers_default'))


#subtitle
APPID = config.get('subtitle', 'appId')
APPSECRET = config.get('subtitle', 'appSecret')
# 初始化日志系统
init_logging()
