from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .serializers import (
                          UserSerializer, RegistrationSerializer, 
                          SetPasswordSerializer, FollowSerializer)
from .permissions import UserRegistration
from .models import Follow

User = get_user_model()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'delete']
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)
    permission_classes = (UserRegistration,)

    def get_serializer_class(self):
        if self.action == 'create':
            return RegistrationSerializer
        return UserSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(permissions.IsAuthenticated,),
        serializer_class=UserSerializer,
        url_path='me'
    )
    def user_info(self, request, pk=None):
        return Response(self.get_serializer(request.user).data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=(permissions.IsAuthenticated,),
        url_path='set_password'
    )
    def set_password(self, request, pk=None):
        user = request.user
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        check_pwd = bool(
            user.password == serializer.data['current_password'])
        if check_pwd:
            user.password = serializer.data['new_password']
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise ValidationError(
            {'password': 'Неверный пароль'},
            code='invalid_password',
        )


@api_view(['POST', 'DELETE'])
def follow(request, **kwargs):
    serializer = FollowSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = request.user
    if user.is_authenticated:
        following = get_object_or_404(User, id=kwargs.get('pk'))
        if request.method == 'POST':
            if user.id != following.id:
                follow, created = Follow.objects.get_or_create(
                    user=user, following=following)
                if created:
                    return Response({
                            'email': user.email,
                            'id': user.id,
                            'username': user.username,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'is_subscribed': True,
                    }, status=status.HTTP_201_CREATED)
                raise ValidationError(
                    {'errors': 'Вы уже подписаны на этого автора.'},
                    code='dublicate_errors',
                )
            raise ValidationError(
                    {'errors': 'Вы не можете быть подписаны на самого себя.'},
                    code='id_errors',
                )
        follow = Follow.objects.filter(user=user, following=following)
        if follow.exists():
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise ValidationError({
            'errors': 'Вы не подписаны на этого автора.'},
            code='not_follow_errors',
        )
    return Response(status=status.HTTP_401_UNAUTHORIZED)
