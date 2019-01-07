from . import app_1

@app_1.route('/')
def index():
    return 'hello app 1'
