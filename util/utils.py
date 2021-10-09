# coding:utf-8
from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from pkg.exception import SomethingError
from email.mime.text import MIMEText
import os
import xlrd
import xlwt
import time
import socket
import paramiko
import smtplib
import sqlite3
import traceback
import logging
import json

logger = logging.getLogger("tornado.atp")


def get_workspace(project_dir, workspace):
    """生成对接项目的工作目录"""
    return os.path.join(project_dir, workspace)


def is_number(string):
    """判断字符串是否是数字"""
    try:
        float(string)
        return True
    except ValueError:
        return False
    except TypeError:
        return False


def is_json(string):
    """判断字符串是否是json格式"""
    try:
        json.loads(string)
        return True
    except ValueError:
        return False
    except TypeError:
        return False


def get_dynamic_class(name, options=None):
    """使用type函数，根据名称动态地生成新派生类对象"""

    def initialize(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    if isinstance(options, dict):
        pass
    elif options is None:
        options = {}
    else:
        raise SomethingError("options must be a dictionary or None")
    if isinstance(name, unicode):
        name = name.encode("utf-8")
    new_class = type(name, (object,), options)
    setattr(new_class, "__init__", initialize)

    return new_class


class EmailClient(object):
    def __init__(self, host, port, account, password):
        self.host = host
        self.port = port
        self.account = account
        self.password = password
        self.client = smtplib.SMTP_SSL(self.host, self.port)
        self.client.login(self.account, self.password)

    def send_mail(self, receivers, subject, content):
        try:
            msg = MIMEText(content, 'html', 'utf-8')
            msg['Subject'] = subject
            msg['From'] = self.account
            msg['To'] = ",".join(receivers)
            msg['Accept-Language'] = 'zh-CN'
            msg['Accept-Charset'] = 'ISO-8859-1,utf-8'
            self.client.sendmail(self.account, receivers, msg.as_string())
            print(u"send email successfully")
        except Exception as e:
            print(u"send email fail, detail: {0}".format(e.message))
            print(traceback.format_exc())


class SQLiteHandler(object):
    @staticmethod
    def query(sql, db):
        """连接SQLite数据库并执行查询sql语句，返回执行结果"""
        try:
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            fields = cursor.description
            cursor.close()
            conn.close()
        except Exception as e:
            print(e.message)
            print(traceback.format_exc())
            result = []
            fields = []
        return result, fields

    @staticmethod
    def execute(sql, db):
        """连接SQLite数据库并执行增、删、改的sql语句"""
        try:
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.debug(e.message)
            logger.debug(traceback.format_exc())

    @staticmethod
    def table_already_exist(table_name, db):
        try:
            conn = sqlite3.connect(db)
            cursor = conn.cursor()
            sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            cursor.execute(sql)
            res = cursor.fetchall()
            result = [i[0] for i in res if i[0] == table_name]
            cursor.close()
            conn.close()
            return True if result else False
        except Exception as e:
            logger.debug(e.message)
            logger.debug(traceback.format_exc())


class ExcelBuild(object):
    def __init__(self, sheet_list=None):
        self.workbook = xlwt.Workbook()
        self.sheet_list = ["Sheet1"] if sheet_list is None else sheet_list
        self.setup()

    def setup(self):
        """
        根据sheet列表初始化创建sheet页对象和初始化光标所在行row等于0
        """
        for name in self.sheet_list:
            setattr(self, "{0}_sheet".format(name), self.workbook.add_sheet(name, cell_overwrite_ok=True))
            setattr(self, "{0}_row".format(name), 0)

    def cell(self, sheet_name, row, col, content):
        """
        对sheet文本对象某个单元格内容进行新增或修改。
        :param sheet_name: sheet表名
        :param row: 行数
        :param col: 列数
        :param content: 填写内容
        """
        sheet = self.get_sheet(sheet_name)
        sheet.write(row, col, content)

    def list_add(self, sheet_name, col_list, row=None):
        """
        在sheet文本对象末尾新增行，并对该行所有单元表格填写内容，该操作结束后会自动换行
        :param sheet_name: sheet表名
        :param col_list: 内容列表，包含一行所有单元格的内容
        :param row: 行数,如果未指定行，则默认为末尾行
        """
        sheet = self.get_sheet(sheet_name)
        row = self.get_row(sheet_name) if row is None else row
        if not isinstance(col_list, (list, tuple)):
            raise AssertionError(u"参数'col_list'必须是一个列表或者元组数据".format())
        for index, content in enumerate(col_list):
            sheet.write(row, index, content)
        self.set_row(sheet_name, row + 1)

    def get_row(self, sheet_name):
        """
        获得sheet页文本对象当前末尾行的row数
        :param sheet_name: sheet表名
        """
        return getattr(self, "{0}_row".format(sheet_name))

    def get_sheet(self, sheet_name):
        """
        获得sheet页文本对象
        :param sheet_name: sheet表名
        """
        return getattr(self, "{0}_sheet".format(sheet_name))

    def set_row(self, sheet_name, row):
        """
        修改sheet页文本对象光标所在的行数（默认光标是在末尾行处）
        :param sheet_name: sheet表名
        :param row: 行数
        """
        setattr(self, "{0}_row".format(sheet_name), row)

    def save(self, file_path):
        """
        保存当前excel文本对象到文件中
        :param file_path: 文件路径
        """
        self.workbook.save(file_path)


class ThreadPoolTaskRunner(object):
    """
    初始化线程池，run函数异步执行目标函数，tornado gen.coroutine + yield 获得执行结果数据
    """
    def __init__(self, pool_max=None, loop=None):
        self.executor = ThreadPoolExecutor(pool_max)
        self.loop = loop or IOLoop.current()

    @run_on_executor
    def run(self, func, args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}
        return func(*args, **kwargs)


class DynamicCache(object):
    """
    简单的缓存模型，用于缓存动态创建的项目对接数据表orm模型对象
    """

    def __init__(self):
        self._cache = dict()

    def get(self, name):
        return self._cache.get(name)

    def put(self, name, obj):
        self._cache[name] = obj

    def all(self):
        return self._cache.keys()

    def remove(self, name):
        self._cache.pop(name)

    def clear(self):
        self._cache.clear()


def read_parameters_instances_from_excel(file_path):
    excel_file = xlrd.open_workbook(file_path)
    sheet = excel_file.sheet_by_index(0)
    lst = [[j.value for j in i] for i in sheet.get_rows()][1:]
    ret = dict()
    for i in lst:
        ret[i[0]] = i[1:]
    return ret


def get_current_day():
    """
    获取当前时间，例如：2019-12-20 13:29:20
    :return: str
    """
    return time.strftime("%Y-%m-%d")


def convert_timestamp_to_format_time(timestamp):
    """
    将时间戳转换为标准时间格式
    :param timestamp, str, e.g. 1606728936或1609922687349
    :return: str
    """
    timestamp = timestamp if len(timestamp) == 10 else timestamp[:10]
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(timestamp)))


class SSHServer(object):
    """
    此类通过SSH连接server，提供远程方式执行命令，上传下载文件（目前只支持普通类型文件）
    """
    def __init__(self, ip, username, password):
        """
        Initialize class
        :param ip: string, ip address of server to ssh to
        :param username: string, server username
        :param password: string, server password
        """
        if not self._check_ip_reachable(ip):
            raise RuntimeError("ip: {} is not reachable".format(ip))

        logger.info("Initialize ssh server: %s" % ip)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password)

        conn = paramiko.Transport((ip, 22))
        conn.connect(username=username, password=password)

        self.ip = ip
        self.sftp = paramiko.SFTPClient.from_transport(conn)
        self.ssh = ssh

    def _check_ip_reachable(self, ip, port=22):
        """
        check if ip reachable
        :param ip: string, ip address
        :param port: int, port to check
        :return: boolean, True for ip reachable, False for not reachable
        """
        reachable = True
        try:
            logger.debug("Connecting to {0} on port {1}".format(ip, port))
            socket.create_connection((ip, port))
        except socket.error as exception:
            logger.debug("Connection to {0} on port {1} failed: {2}".format(ip, port, exception))
            reachable = False

        return reachable

    def run(self, command, check_rc=True):
        """
        run command against remote server via ssh
        :param command: string, e.g. 'ls'
        :param check_rc: boolean, True for check return code. if return code is not zero, throw exception
        :return: dict, containing 'stderr', 'stdout', 'rc'
        """
        logger.info("[{0}]: {1}".format(self.ip, command))
        _, ssh_stdout, ssh_stderr = self.ssh.exec_command(command)

        stdout = ssh_stdout.read()
        stderr = ssh_stderr.read()
        return_rc = ssh_stdout.channel.recv_exit_status()

        if return_rc:
            logger.debug("[{0}][rc: {1}]: {2}".format(command, return_rc, stderr))
            if check_rc:
                raise RuntimeError("\nReturn code: {0}\nError:\n{1}".format(return_rc, stderr))
        else:
            logger.debug("[{0}]: {1}".format(command, stdout))
        result = {
            'stdout': stdout,
            'stderr': stderr,
            'rc': return_rc
        }
        return result


if __name__ == "__main__":
    def test(day_id=get_current_day()):
        print(day_id)

    test()




