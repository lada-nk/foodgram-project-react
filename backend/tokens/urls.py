from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import token_obtain, token_destroy

app_name = 'tokens'

router = DefaultRouter()

urlpatterns = [
    path('token/login/', token_obtain, name='token_obtain'),
    path('token/logout/', token_destroy, name='token_destroy'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
