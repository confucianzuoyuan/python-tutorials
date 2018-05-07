from django.conf.urls import url
from frontend import views
urlpatterns = [
    url(r'^', views.index)
]