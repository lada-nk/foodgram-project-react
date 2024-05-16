from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt import tokens

from .serializers import (
                          UserSerializer, UserInfoSerializer,
                          RegistrationSerializer, TokenObtainSerializer)

User = get_user_model()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'delete']
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    def get_serializer_class(self):
        if self.action == 'create':
            return RegistrationSerializer
        return UserSerializer

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=UserInfoSerializer,
        url_path='me'
    )
    def user_info(self, request, pk=None):
        return Response(self.get_serializer(request.user).data)


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
