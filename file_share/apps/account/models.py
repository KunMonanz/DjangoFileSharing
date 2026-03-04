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


class FriendshipRequest(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending"
        ACCEPTED = "accepted"

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
    receiver = models.ForeignKey(
        User,
        related_name="friendship_receiver",
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sender", "receiver"],
                name="unique_friend_request"
            )
        ]
