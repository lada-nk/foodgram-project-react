from django.contrib import admin
from django.urls import include, path, re_path

api_urls = [
    path('users/', include('users.urls')),
    path('', include('recipes.urls')),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    re_path(r'', include('shortlink.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urls)),
]
