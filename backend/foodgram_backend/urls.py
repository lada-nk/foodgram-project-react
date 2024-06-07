from django.contrib import admin
from django.urls import path, include

api_urls = [
    path('users/', include('users.urls')),
    # path('auth/', include('tokens.urls')),
    path('', include('recipes.urls')),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urls)),
]
