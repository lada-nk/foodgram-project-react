from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


from .serializers import (FollowSerializer, AvatarSerializer, UserSerializer)
from .models import Follow
from .pagination import LimitPageNumberPagination

User = get_user_model()


class UserViewSet(UserViewSet):
    """Вьюсет для пользователей."""

    pagination_class = LimitPageNumberPagination

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,),
            serializer_class=UserSerializer, url_path='me')
    def me(self, request, pk=None):
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

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, id):
        user = request.user
        following = get_object_or_404(User, id=id)
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
