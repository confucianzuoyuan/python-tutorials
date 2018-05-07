"""bookstore URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url

from rest_framework.routers import DefaultRouter
from users import views as users_views
from books import views as books_views
router = DefaultRouter()
router.register(r'users', users_views.PassportViewSet)
router.register(r'address', users_views.AddressViewSet)
router.register(r'books', books_views.BooksViewSet)

API_TITLE = 'Bookstore API'
API_DESCRIPTION = 'Bookstore API'

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^', include(router.urls)),
    url(r'^index/', include('frontend.urls')),
]