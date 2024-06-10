from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, RecipeViewSet,
                    TagViewSet, UserViewSet)

app_name = 'api'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
