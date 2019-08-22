from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from pita import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL)

    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

comic_patterns = [
    path('<slug:slug>/<int:number>', views.view_comic, name='comic_page'),
    path('<slug:slug>', views.view_comic, name='comic'),

    path('', views.comic_index, name='comic_index'),
]

urlpatterns += [
    path('', views.index, name='index'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('comics/', include(comic_patterns)),
    url(r'^(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$', views.page, name='page'),
]
