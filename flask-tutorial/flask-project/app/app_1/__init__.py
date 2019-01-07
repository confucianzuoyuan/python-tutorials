from flask import Blueprint

app_1 = Blueprint('app_1', __name__)

from . import views
