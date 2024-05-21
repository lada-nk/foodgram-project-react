from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt import tokens

from .serializers import TokenObtainSerializer

User = get_user_model()


@api_view(['POST'])
def token_obtain(request):
    serializer = TokenObtainSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.data['email']
    user = get_object_or_404(User, email=email)
    check_pwd = bool(
        user.password == serializer.data['password']
    )
    if check_pwd:
        return Response({
            'auth_token': str(tokens.RefreshToken.for_user(user).access_token)
            })
    raise ValidationError(
        {'password': 'Неверный пароль'},
        code='invalid_password',
    )


@api_view(['POST'])
def token_destroy(request):
    user = request.user
    if user.is_authenticated:
        tokens.RefreshToken.for_user(user).blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(status=status.HTTP_401_UNAUTHORIZED)
