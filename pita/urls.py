from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin

from pita import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL)

    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

urlpatterns += [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$', views.page, name='page'),
]
