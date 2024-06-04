from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


from .serializers import (UserSerializer, RegistrationSerializer,
                          SetPasswordSerializer, FollowSerializer,
                          AvatarSerializer)
from .permissions import UserRegistration
from .models import Follow
from .pagination import LimitPageNumberPagination

User = get_user_model()


class UserViewSet(ModelViewSet):
    """"Вьюсет для пользователей."""

    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    search_fields = ('username',)
    permission_classes = (UserRegistration,)
    pagination_class = LimitPageNumberPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return RegistrationSerializer
        return UserSerializer

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,),
            serializer_class=UserSerializer, url_path='me')
    def user_info(self, request, pk=None):
        return Response(self.get_serializer(request.user).data)

    @action(detail=False, methods=['put', 'patch', 'delete'],
            permission_classes=(permissions.IsAuthenticated,),
            url_path='me/avatar')
    def user_avatar(self, request, pk=None):
        user = self.request.user
        if self.request.method == 'DELETE':
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(
            user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'],
            permission_classes=(permissions.IsAuthenticated,))
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
            code='invalid_password')

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, pk):
        user = request.user
        following = get_object_or_404(User, id=pk)
        if request.method == 'DELETE':
            follow = Follow.objects.filter(user=user, following=following)
            if not follow.exists():
                raise ValidationError(
                    {'errors': f'Вы не подписаны на автора'
                     f' {following.username}.'},
                    code='not_follow_errors')
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if user.id == following.id:
            raise ValidationError(
                {'errors': 'Вы не можете быть подписаны на самого себя'},
                code='id_errors')
        follow, created = Follow.objects.get_or_create(
            user=user, following=following)
        if not created:
            raise ValidationError(
                {'errors': f'Вы уже подписаны на автора {following.username}'},
                code='dublicate_errors')
        serializer = FollowSerializer(
            following, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request, pk=None):
        serializer = FollowSerializer(
            self.paginate_queryset(
                [follow.following for follow in request.user.follower.all()]),
            many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
