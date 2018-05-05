# coding: utf-8

import logging
import hashlib
import config
import re

from tornado.web import RequestHandler
from handlers.BaseHandler import BaseHandler

class MessageHandler(BaseHandler):
    def post(self):
        # 获取参数
        username = self.json_args.get("username", "")
        useraddress = self.json_args.get("useraddress", "")
        email = self.json_args.get("email", "")
        messagetext = self.json_args.get("messagetext", "")

        sql = "insert into message(username, useraddress, email, messagetext) values(%(username)s, %(useraddress)s, %(email)s, %(messagetext)s);"
        try:
            res = self.db.execute(sql, username=username, useraddress=useraddress, email=email, messagetext=messagetext)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=500, errmsg="留言失败"))

        self.write(dict(errcode=200, errmsg="留言成功"))

