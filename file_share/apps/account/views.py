from django.db import transaction
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404


from rest_framework import exceptions, generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from file_share.apps.notification.factory import NotificationFactory
from file_share.apps.notification.models import Notification

from .models import FriendshipRelationship

from .serializers import (
    MyTokenObtainPairSerializer,
    UserRegisterSerializer,
    MiniUserSerializer,
    FriendRequestsSerializer,
)

User = get_user_model()

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterUserView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]


class GetAllFriendsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MiniUserSerializer

    def get_queryset(self):
        return self.request.user.friends.all().order_by('username')


class SendFriendRequest(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = self.request.user

        reciever_id = self.kwargs.get("reciever_id")
        reciever = get_object_or_404(User, id=reciever_id)

        friendship_created = FriendshipRelationship.objects.create(
            sender=user,
            reciever=reciever
        )

        if reciever == user:
            return Response({
                "error": "Cannot send a friend request to yourself"
            },
                status=status.HTTP_403_FORBIDDEN
            )

        if friendship_created:
            with transaction.atomic():
                notification_factory = NotificationFactory()

                notification_factory.create_notification(
                    recipient=user,  # type: ignore
                    message_type=Notification.NotificationType.FRIENDSHIP_REQUEST_SENT,
                    activator=reciever  # type: ignore
                )
                notification_factory.create_notification(
                    recipient=reciever,  # type: ignore
                    message_type=Notification.NotificationType.FRIENDSHIP_REQUEST_RECIEVED,
                    activator=user  # type: ignore
                )

            return Response(
                {
                    "message": "Friend request send successfully"
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                "error": "Failed to create friendship request"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class RemoveFriendRequest(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = self.request.user

        reciever_id = self.kwargs.get("reciever_id")
        reciever = get_object_or_404(User, id=reciever_id)

        friendship_request_exists = get_object_or_404(
            FriendshipRelationship,
            sender=user,
            reciever=reciever
        )

        if friendship_request_exists:
            friendship_request_exists.delete()

            return Response(
                {
                    "message": "Friendship request deleted successfully"
                },
                status=status.HTTP_200_OK
            )


class AcceptFriendRequest(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user = self.request.user

        friend_request_id = self.kwargs.get("friend_request_id")

        friend_request = get_object_or_404(
            FriendshipRelationship,
            id=friend_request_id
        )

        sender = friend_request.sender
        reciever = friend_request.reciever

        if reciever != user:
            return exceptions.PermissionDenied(
                "You are unauthorized!"
            )

        if friend_request.is_accepted == True:
            return Response(
                {
                    "error": "Friendship request has already been accepted"
                },
                status=status.HTTP_208_ALREADY_REPORTED
            )

        with transaction.atomic():
            friend_request.is_accepted = True
            friend_request.save()

            notification_factory = NotificationFactory()
            notification_factory.create_notification(
                recipient=reciever,
                message_type=Notification.NotificationType.FRIENDSHIP_REQUEST_ACCEPTED,
                activator=user  # type: ignore
            )

            reciever.friends.add(sender)

        return Response(
            {
                "message": "Friend request accepted successfully"
            },
            status=status.HTTP_200_OK
        )


class GetAllFriendRequests(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FriendRequestsSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = FriendshipRelationship.objects\
            .select_related('reciever', 'sender')\
            .filter(sender=user)

        unaccepted_only = self.request.query_params.get('is_accepted')
        if unaccepted_only == 'true':
            queryset.filter(is_accepted=False)

        return queryset
