from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('accounts.urls')),
    # Serve uploaded media in production too (static() only works when DEBUG=True)
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]