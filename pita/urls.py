from django.conf.urls import url
from django.contrib import admin

from pita import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$', views.page, name='page'),
]
