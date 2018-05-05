# coding: utf-8
import logging

from handlers.BaseHandler import BaseHandler

from tornado import gen
import tornado_mysql

class MessageHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        # 获取参数
        print(self.json_args)
        username = self.json_args.get("username", "")
        useraddress = self.json_args.get("useraddress", "")
        email = self.json_args.get("email", "")
        messagetext = self.json_args.get("messagetext", "")

        conn = yield tornado_mysql.connect(host='127.0.0.1', port=3306, user='root', passwd='', db='messageboard')
        cur = conn.cursor()
        sql = "INSERT INTO message (username, useraddress, email, messagetext) VALUES ('%s', '%s', '%s', '%s');" % (username, useraddress, email, messagetext)


        try:
            yield cur.execute(sql)
            yield cur.execute("SELECT * FROM message")
            for row in cur:
                print(row)
            yield conn.commit()
            raise gen.Return(dict(errcode=200, errmsg="留言成功"))        
        except Exception as e:
            logging.error(e)
            raise gen.Return(dict(errcode=500, errmsg="留言失败"))
        finally:
            cur.close()
            conn.close()
        

