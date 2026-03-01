from rest_framework import generics, permissions

from file_share.apps.notification.models import Notification
from file_share.apps.notification.serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        # Always optimize with select_related to avoid N+1 queries
        queryset = Notification.objects.select_related(
            'user').filter(user=self.request.user)

        # Check for ?unread=true in the URL
        unread_only = self.request.query_params.get('unread')
        if unread_only == 'true':
            queryset = queryset.filter(is_read=False)

        return queryset.order_by('-created_at')


class RetrieveNotification(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'notification_id'

    def get_queryset(self):
        user = self.request.user
        return Notification.objects\
            .select_related('user')\
            .filter(user=user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_read:
            instance.is_read = True
            instance.save(update_fields=['is_read'])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
