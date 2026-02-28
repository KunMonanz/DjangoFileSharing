from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import exceptions, generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import FriendshipRelationship

from .serializers import (
    MyTokenObtainPairSerializer,
    UserRegisterSerializer,
    MiniUserSerializer
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
        user = self.request.user
        return user.friends.all()


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

        if friendship_created:
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
                }
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

        friend_request.is_accepted = True
        reciever.friends.add(sender)

        return Response(
            {
                "message": "Friend request accepted successfully"
            }
        )
