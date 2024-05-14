from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet, token_obtain, registration
)

app_name = 'api'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

auth = [
    path('token/', token_obtain, name='token_obtain'),
    path('signup/', registration, name='signup'),
]

api_urls = [
    path('', include(router.urls)),
    path('auth/', include(auth)),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
