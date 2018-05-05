import os

from handlers.BaseHandler import StaticFileBaseHandler as StaticFileHandler
from handlers import MessageBoard

urls = [
    (r"/api/submit", MessageBoard.MessageHandler),
    (r"/(.*)", StaticFileHandler,
     dict(path=os.path.join(os.path.dirname(__file__), "html"), default_filename="messageboard.html"))
]