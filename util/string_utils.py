# coding:utf-8
import datetime
import random
import string
from Crypto.Cipher import AES
import base64
import hashlib
from util.settings import GLOBAL_AES_KEY
import time
from hashlib import sha256
import hmac


class StringUtils(object):

    @staticmethod
    def generate_random_str(randomlength=10, is_digits_only=False):
        """
        生成一个指定长度的随机字符串，其中
        string.digits=0123456789
        string.ascii_letters=abcdefghigklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
        """

        if is_digits_only:
            str_list = [random.choice(string.digits) for i in range(randomlength)]
        else:
            str_list = [random.choice(string.digits + string.ascii_letters) for i in range(randomlength)]
        random_str = ''.join(str_list)
        return random_str

    @staticmethod
    def date2str(date_obj, str_format='%Y-%m-%d %H:%M:%S'):
        if date_obj and isinstance(date_obj, datetime.datetime):
            return date_obj.strftime(str_format)
        else:
            return date_obj

    @staticmethod
    def aes_decrypt(text, key=GLOBAL_AES_KEY):
        mode = AES.MODE_ECB
        cryptor = AES.new(key, mode)
        result = cryptor.decrypt(base64.b64decode(text)).decode('utf-8')
        return result[:-ord(result[-1])]

    @staticmethod
    def aes_encrypt(text, key=GLOBAL_AES_KEY):
        mode = AES.MODE_ECB
        padding = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16)
        cryptos = AES.new(key, mode)
        cipher_text = cryptos.encrypt(padding(text).encode("utf-8"))
        return base64.b64encode(cipher_text).decode("utf-8")

    @staticmethod
    def md5_encrypt(text, encoding='utf-8'):
        input_name = hashlib.md5()
        input_name.update(text.encode(encoding))
        return input_name.hexdigest()

    @staticmethod
    def get_key_amber_upload():
        date_md5 = StringUtils.md5_encrypt(time.strftime('%Y%m%d'))
        length = len(date_md5)
        key = ''
        if length > 16:
            key = date_md5[1:17]
        else:
            key = date_md5 + '0' * (16 - length)
        return key

    @staticmethod
    def get_sign(data, key):
        key = key.encode('utf-8')
        message = data.encode('utf-8')
        h = hmac.new(key, message, digestmod=sha256)
        sign = h.hexdigest()
        return sign


if __name__ == '__main__':
    # key = StringUtils.get_key_amber_upload()
    a = {"a":"a"}
    print(type(a))
    # print(StringUtils.get_sign("roomId=329576638&applicationId=830125609689546752&currentTimeStamp=1631178951716&random=92177074", "wwfumcxpkfkdyxuwfh929mw5mmgv7a3syhr3pvpcr1ck80og8ov3hoa844rpbrc7yegech64a1ety0w6em897c8l9z9v9zwheuym7o8bawpx95axtwn60bs50njvby5i"))
