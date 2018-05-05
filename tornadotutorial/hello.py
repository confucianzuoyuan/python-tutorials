import tornado.ioloop
import tornado.web
from tornado import gen
from tornado.httpclient import AsyncHTTPClient

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("hahahaha")

class GenAsyncHandler(tornado.web.RequestHandler):
    # @gen_coroutine
    @gen.coroutine
    def get(self):
        http_client = AsyncHTTPClient()
        # yield long_io()
        # yield Request(url)
        response = yield http_client.fetch("http://example.com")
        self.write("gen")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/index", IndexHandler),
        (r"/gen", GenAsyncHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()