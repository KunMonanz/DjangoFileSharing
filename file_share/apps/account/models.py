import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )

    friends = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True
    )


class FriendshipRelationship(models.Model):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )
    sender = models.ForeignKey(
        User,
        related_name="friendship_sender",
        on_delete=models.CASCADE
    )
    reciever = models.ForeignKey(
        User,
        related_name="friendship_reciever",
        on_delete=models.CASCADE
    )
    is_accepted = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
