from django.contrib.auth import get_user_model
# from django.shortcuts import get_object_or_404
# from rest_framework import filters, permissions, status
# from rest_framework.decorators import action, api_view
# from rest_framework.exceptions import ValidationError
# from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

# from .serializers import (
#                           UserSerializer, RegistrationSerializer, 
#                           SetPasswordSerializer, FollowSerializer)
# from .permissions import UserRegistration
# from .models import Follow

User = get_user_model()


class RecipeViewSet(ModelViewSet):
    pass
