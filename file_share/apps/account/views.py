import logging

from django.db import transaction
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import exceptions, generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from file_share.apps.notification.factory import NotificationFactory

from file_share.apps.notification.models import Notification

from .models import FriendshipRequest

from .serializers import (
    MyTokenObtainPairSerializer,
    UserRegisterSerializer,
    MiniUserSerializer,
    FriendRequestsSerializer,
)

User = get_user_model()

logger = logging.getLogger(__name__)

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterUserView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            logger.info(
                "START: Registering new user"
            )
            response = super().post(request, *args, **kwargs)
            return response
        except Exception as e:
            logger.exception(
                "CRITICAL: Database error in creating user"
            )
            raise e


class GetAllFriendsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MiniUserSerializer

    def get_queryset(self):
        return self.request.user.friends.all().order_by('username')

    def list(self, request, *args, **kwargs):
        user = self.request.user
        try:
            response = super().list(request, *args, **kwargs)
            data = response.data
            count = data.get('count') if isinstance(data, dict) else len(data)

            logger.info(
                f"SUCCESS: Retrieved {count} friends of user={user.id}"
            )
            return response
        except Exception as e:
            logger.exception(
                f"CRITICAL: Database failure in retrieving friends of user={user.id}"
            )
            raise e

class SendFriendRequest(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = self.request.user

        receiver_id = self.kwargs.get("receiver_id")
        receiver = get_object_or_404(User, id=receiver_id)

        logger.info(
            f"START: User={user.id} is attempting to send a friend request to user={receiver.id}"
        )


        if receiver == user:
            logger.warning(
                f"SECURITY: User={user.id} attempted to send a friend request to themselves"
            )
            return Response({
                "error": "Cannot send a friend request to yourself"
            },
                status=status.HTTP_403_FORBIDDEN
            )

        if FriendshipRequest.objects.filter(
            sender=user,
            receiver=receiver
        ).exists():

            logger.info(
                f"LOGIC: User={user.id} attempted to resend a friend request to {receiver.id}"
            )
            return Response(
                {
                    "error": "You have sent a friend request to this user before"
                }
            )

        if FriendshipRequest.objects.filter(
            sender=receiver,
            receiver=user
        ).exists():

            logger.info(
                f"LOGIC: Friend ship request snet to user={receiver.id} by user{user.id} because user={receiver.id} has already sent a request"
            )
            return Response(
                {
                    "error": f"{receiver.username} has sent you a friend request, go ahead and accept it"
                }
            )

        if user.friends.filter(id=receiver.id).exists():
            return Response(
                {"error": "You are already friends"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            with transaction.atomic():

                FriendshipRequest.objects.create(
                    sender=user,
                    receiver=receiver
                )

                notification_factory = NotificationFactory()

                notification_factory.create_notification(
                    recipient=user,  # type: ignore
                    message_type=Notification.NotificationType.FRIENDSHIP_REQUEST_SENT,
                    activator=receiver  # type: ignore
                )
                notification_factory.create_notification(
                    recipient=receiver,  # type: ignore
                    message_type=Notification.NotificationType.FRIENDSHIP_REQUEST_RECEIVED,
                    activator=user  # type: ignore
                )
            logger.info(
                f"SUCCESS: User={user.id} successfully sent a friend request to {receiver.id}"
            )
            return Response(
                {
                    "message": "Friend request send successfully"
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.exception(
                f"CRITICAL: Database error in user={user.id} sending a friend request to {receiver.id}"
            )
            raise e



class RemoveFriendRequest(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = self.request.user

        receiver_id = self.kwargs.get("receiver_id")
        receiver = get_object_or_404(User, id=receiver_id)

        logger.info(
            f"START: Removing a friend request to user={user.id} sent by {receiver.id}"
        )

        friendship_request_exists = \
            FriendshipRequest.objects.filter(
                sender=user,
                receiver=receiver
            ).first()\
            or\
            FriendshipRequest.objects.filter(
                sender=receiver,
                receiver=user
            ).first()

        if not friendship_request_exists:
            return Response({"error": "No friendship request found"}, status=404)

        try:
            friendship_request_id = friendship_request_exists.id
            friendship_request_exists.delete()
            logger.info(
                f"SUCCESS: Deleted friend request {friendship_request_id} from {user.id} sent to {receiver.id}"
            )
            return Response(
                {
                    "message": "Friendship request deleted successfully"
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.exception(
                f"CRITICAL: Database error, user={user.id} failed to delete a friend request {friendship_request_exists.id} to user {receiver.id}"
            )
            raise e


class AcceptFriendRequest(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user = self.request.user

        friend_request_id = self.kwargs.get("friend_request_id")

        friend_request = get_object_or_404(
            FriendshipRequest,
            id=friend_request_id,
            receiver=user
        )

        sender = friend_request.sender
        receiver = friend_request.receiver

        logger.info(
            f"START: User={user.id} accepting friend request {friend_request.id} from {sender.id}"
        )

        if receiver != user:
            logger.error(
                f"SECURITY: User={user.id} attempted to accept friendship request {friend_request.id} when he/she was not the receiver"
            )
            raise exceptions.PermissionDenied(
                "You are unauthorized to accept this friendship request!"
            )

        if friend_request.status == FriendshipRequest.Status.ACCEPTED:
            logger.error(
                f"LOGIC: User={user.id} attempted to accept already accepted friendship request {friend_request.id}"
            )
            return Response(
                {
                    "error": "Friendship request has already been accepted"
                },
                status=status.HTTP_409_CONFLICT
            )
        try:
            with transaction.atomic():

                friend_request.status = FriendshipRequest.Status.ACCEPTED
                friend_request.save()

                notification_factory = NotificationFactory()
                notification_factory.create_notification(
                    recipient=receiver,
                    message_type=Notification.NotificationType.FRIENDSHIP_REQUEST_ACCEPTED,
                    activator=user  # type: ignore
                )
                friend_request.status = FriendshipRequest.Status.ACCEPTED
                friend_request.save()

                receiver.friends.add(sender)
                friend_request.delete()

            logger.info(
                f"SUCCESS: User={user.id} accepted friend request {friend_request.id}"
            )

            return Response(
                {
                    "message": "Friend request accepted successfully"
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception(
                f"CRITICAL: Database error failed to accept friend request {friend_request.id} for user {user.id}"
            )
            raise e


class GetAllReceivedFriendRequests(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FriendRequestsSerializer

    def get_queryset(self):  # type: ignore
        user = self.request.user

        logger.info(
            f"START: Attempting to retrieve all received friendship requests for user={user.id}"
        )

        queryset = FriendshipRequest.objects\
            .select_related('receiver', 'sender')\
            .filter(receiver=user)

        return queryset.order_by('-created')

    def list(self, request, *args, **kwargs):
        user = self.request.user

        try:
            response = super().list(request, *args, **kwargs)
            data = response.data
            count = data.get("count") if isinstance(data, dict) else len(data)
            logger.info(
                f"SUCCESS: Retrieved {count} friendship requests received by {user.id}"
            )
            return response

        except Exception as e:
            logger.exception(
                f"CRITICAL: Database error to retrieve friendship requests for user={user.id}"
            )
            raise e


class GetAllSentFriendRequests(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FriendRequestsSerializer

    def get_queryset(self):  # type: ignore
        user = self.request.user

        logger.info(
            f"START: Attempting to get all friendship request by user={user.id}"
        )

        queryset = FriendshipRequest.objects\
            .select_related('receiver', 'sender')\
            .filter(sender=user)

        return queryset.order_by('-created')

    def list(self, request, *args, **kwargs):
        user = self.request.user

        try:
            response = super().list(request, *args, **kwargs)
            data = response.data
            count = data.get("count") if isinstance(data, dict) else len(data)

            logger.info(
                f"SUCCESS: Fetched {count} friendship requests sent to user={user.id}"
            )
            return response

        except Exception as e:
            logger.exception(
                f"CRITICAL: Database error failed to fetch friend requests sent to user={user.id}"
            )
            raise e


class RemoveFriend(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        friend_id = kwargs.get('friend_id')

        friend = get_object_or_404(User, id=friend_id)

        if not user.friends.filter(id=friend.id).exists():
            return Response(
                {"error": "You are not friends with this user"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.friends.remove(friend)

        return Response(
            {"message": "Friend removed successfully"},
            status=status.HTTP_200_OK
        )
