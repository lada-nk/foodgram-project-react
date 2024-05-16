from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet, token_obtain
)

app_name = 'users'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

auth = [
    path('token/login/', token_obtain, name='token_obtain'),
]

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include(auth)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
