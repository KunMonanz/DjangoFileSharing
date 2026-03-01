from rest_framework import serializers

from .models import Notification
from file_share.apps.account.serializers import MiniUserSerializer


class NotificationSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer()

    class Meta:
        model = Notification
        fields = [
            'id',
            'user',
            'message',
            'created_at'
        ]
