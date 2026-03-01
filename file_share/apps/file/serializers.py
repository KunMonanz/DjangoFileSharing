import filetype
import mimetypes

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.contrib.humanize.templatetags.humanize import naturaltime

from rest_framework import serializers
from .models import File, FileShare
from file_share.apps.account.serializers import MiniUserSerializer


def human_readable_size(size: int):
    if size < 0:
        raise ValueError("Size cannot be negative")

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size_float = float(size)

    for unit in units:
        if size_float < 1024 or unit == units[-1]:
            return f"{size_float:.2f} {unit}"
        size_float /= 1024


class FileUploadSerializer(serializers.ModelSerializer):
    size = serializers.SerializerMethodField(read_only=True)
    uploaded_at = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            "id",
            "file",
            "size",
            "uploaded_at"
        ]
        read_only_fields = ["id", "size", "uploaded_at"]

    def validate_file(self, file: UploadedFile) -> UploadedFile:
        if file.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            raise serializers.ValidationError(
                "File too large. Max size is 5MB."
            )

        file_header = file.read(261)
        file.seek(0)

        detected_type = filetype.guess(file_header)

        allowed_types = {
            # binary
            "image/png", "image/jpeg", "image/jpg", "image/gif",
            "image/webp", "image/bmp", "image/tiff",
            "video/mp4", "video/webm", "video/ogg", "video/quicktime",

            # text
            "text/plain", "text/csv", "text/markdown", "application/json",
        }

        if detected_type is None:
            # Try fallback for text files
            text_mime, _ = mimetypes.guess_type(file.name)
            if text_mime not in allowed_types:
                raise serializers.ValidationError(
                    f"Invalid file type: {text_mime or 'unknown'}"
                )
        else:
            if detected_type.mime not in allowed_types:
                raise serializers.ValidationError(
                    f"Invalid file type: {detected_type.mime}"
                )

        return file

    def get_size(self, file: File):
        return human_readable_size(file.file.size)

    def get_uploaded_at(self, file: File):
        return naturaltime(file.uploaded_at)

class FileSerializer(serializers.ModelSerializer):
    owner = MiniUserSerializer(read_only=True)
    size = serializers.SerializerMethodField(read_only=True)
    uploaded_at = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            "id",
            "owner",
            "name",
            "size",
            "uploaded_at"
        ]
        read_only_fields = [
            "id",
            "owner",
            "content_type"
            "size",
            "uploaded_at"
        ]

    def get_size(self, file: File):
        return human_readable_size(file.file.size)

    def get_uploaded_at(self, file: File):
        return naturaltime(file.uploaded_at)

class MiniFileSerializer(serializers.ModelSerializer):
    owner = MiniUserSerializer(read_only=True)
    size = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = File
        fields = [
            "id",
            "owner",
            "name",
            "content_type",
            "size"
        ]
        read_only_fields = [
            "id",
            "owner",
            "content_type",
            "size"
        ]

    def get_size(self, file: File):
        return human_readable_size(file.file.size)


class FileShareSerializer(serializers.ModelSerializer):
    file = MiniFileSerializer()
    shared_at = serializers.SerializerMethodField()

    class Meta:
        model = FileShare
        fields = [
            'id',
            'shared_by',
            'shared_to',
            'file',
            'shared_at',
            'comment',
        ]
        read_only_fields = ['id', 'shared_by', 'shared_at']

    def get_shared_at(self, file_share: FileShare):
        return naturaltime(file_share.shared_at)
