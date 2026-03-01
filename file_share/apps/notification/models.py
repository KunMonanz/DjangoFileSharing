import uuid

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        USER_REGISTRATION = 'USR', 'User Registration'
        FRIENDSHIP_REQUEST_SENT = 'FRS', 'Friendship request sent'
        FRIENDSHIP_REQUEST_ACCEPTED = 'FRA', 'Friendship request accepted'
        FRIENDSHIP_REQUEST_RECIEVED = 'FRR', 'Friendship request recieved'
        OTHER = 'OTH', 'Other'

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )
    user = models.ForeignKey(
        User,
        related_name="notifications",
        on_delete=models.CASCADE
    )
    message = models.TextField(blank=False)
    message_type = models.CharField(
        max_length=3,
        choices=NotificationType.choices,
        default=NotificationType.OTHER
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
