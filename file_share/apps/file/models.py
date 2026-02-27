import uuid
from django.db import models
from file_share.apps.account.models import User


class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="files"
    )

    name = models.CharField(max_length=256, blank=True)
    file = models.FileField(upload_to="files/")
    content_type = models.CharField(max_length=20, blank=False)
    size = models.PositiveBigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)


class FileShare(models.Model):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )

    file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        related_name="shares"
    )

    shared_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shared_files"
    )

    shared_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_files"
    )

    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("file", "shared_to")
