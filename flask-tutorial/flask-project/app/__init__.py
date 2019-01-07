from flask import Flask

def create_app():
    app = Flask(__name__)

    from .app_1 import app_1 as app_1_blueprint
    app.register_blueprint(app_1_blueprint, url_prefix='/app_1')
    # url('^/courses/$', include('courses.urls', namespace='courses'))

    from .app_2 import app_2 as app_2_blueprint
    app.register_blueprint(app_2_blueprint, url_prefix='/app_2')

    return app
