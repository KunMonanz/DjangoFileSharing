from django.contrib.humanize.templatetags.humanize import naturaltime

from rest_framework import serializers

from .models import Notification
from file_share.apps.account.serializers import MiniUserSerializer


class NotificationSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'user',
            'message',
            'is_read',
            'created_at'
        ]

    def get_created_at(self, notifcation: Notification):
        return naturaltime(notifcation.created_at)
