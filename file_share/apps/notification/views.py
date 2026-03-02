import logging
from rest_framework import generics, permissions

from file_share.apps.notification.models import Notification
from file_share.apps.notification.serializers import NotificationSerializer

logger = logging.getLogger(__name__)


class NotificationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        unread_only = self.request.query_params.get('unread')

        logger.info(
            f"Fetching notifications for user_id={user.id} | unread_only={unread_only}"
        )

        try:
            queryset = Notification.objects.select_related(
                'user').filter(user=user)

            if unread_only == 'true':
                queryset = queryset.filter(is_read=False)

            return queryset.order_by('-created_at')

        except Exception as e:
            logger.error(
                f"Failed to retrieve notifications for user {user.id}: {str(e)}")
            return Notification.objects.none()


class RetrieveNotification(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'notification_id'

    def get_queryset(self):
        return Notification.objects.select_related('user').filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        notification_id = kwargs.get('notification_id')

        logger.info(
            f"Attempting to fetch notification {notification_id} for user_id={user.id}")

        try:
            instance = self.get_object()

            if not instance.is_read:
                instance.is_read = True
                instance.save(update_fields=['is_read'])

            serializer = self.get_serializer(instance)
            logger.info(
                f"SUCCESS: User {user.id} retrieved and read notification {notification_id}"
            )

            return Response(serializer.data)

        except Exception as e:
            logger.exception(
                f"ERROR: Failed retrieval of notification {notification_id} for user {user.id}")
            raise e
