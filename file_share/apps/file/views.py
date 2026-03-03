from rest_framework import generics, permissions
from django.db import transaction
import logging

from django.db.models import Q
from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions, exceptions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.throttling import ScopedRateThrottle

from .models import File, FileShare

from .serializers import (
    FileSerializer,
    FileUploadSerializer,
    FileShareSerializer
)

User = get_user_model()

logger = logging.getLogger(__name__)


class UploadFileCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileUploadSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'sensitive_action'
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        user = self.request.user
        uploaded_file = self.request.FILES.get('file')

        if not uploaded_file:
            logger.warning(
                f"Upload attempt with missing file by user_id={user.id}")  # type: ignore
            raise exceptions.ValidationError(
                "File must be included for upload"
            )

        logger.info(
            f"User {user.id} starting upload: {uploaded_file.name} "
            f"({uploaded_file.size} bytes, {uploaded_file.content_type})"
        )

        try:
            instance = serializer.save(
                owner=user,
                name=uploaded_file.name,
                size=uploaded_file.size,
                content_type=uploaded_file.content_type
            )

            logger.info(
                f"SUCCESS: File ID {instance.id} uploaded for user {user.id}. "
                f"Stored name: {instance.name}"
            )

        except Exception as e:
            logger.exception(
                f"CRITICAL: Upload failed for user {user.id} "  # type: ignore
                f"during file processing: {uploaded_file.name}"
            )
            raise e


class ShareFileCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileShareSerializer

    def perform_create(self, serializer):
        user = self.request.user

        file_id = self.kwargs.get('file_id')
        shared_to_id = self.kwargs.get('user_id')

        logger.info(
            # type: ignore
            f"START: User {user.id} attempting to share file {file_id} with user {shared_to_id}"
        )

        file = get_object_or_404(File, id=file_id)
        shared_to_user = get_object_or_404(User, id=shared_to_id)

        if file.owner != user:
            logger.warning(
                f"SECURITY: User {user.id} tried to share file {file.id} owned by {file.owner.id}"
            )
            raise exceptions.PermissionDenied(
                "You are not permitted to share this file"
            )

        if not user.friends.filter(id=shared_to_user).exists():  # type: ignore
            logger.warning(
                f"LOGIC: User={user.id} tried sharing file={file.id} with non-friend user={shared_to_user.id}"
            )
            raise exceptions.PermissionDenied(
                "You are not permitted to share this file"
            )

        try:
            serializer.save(
                shared_by=user,
                shared_to=shared_to_user,
                file=file
            )
            logger.info(
                # type: ignore
                f"SUCCESS: File={file.id} shared by user={user.id} to  user={shared_to_user.id}"
            )
        except Exception as e:
            logger.exception(
                f"CRITICAL: System failure sharing file={file.id} to user={shared_to_user.id}")  # type: ignore
            raise e


class FileListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileSerializer

    def get_queryset(self):
        user = self.request.user
        # Log the intent/start
        logger.info(
            f"START: Fetching files for user={user.id} (Owner or Shared)")

        # We don't need a try/except here because the query hasn't executed yet.
        return (
            File.objects
            .select_related("owner")
            .filter(
                Q(owner=user) |
                Q(shares__shared_to=user)
            )
            .distinct()
            .order_by('-uploaded_at')
        )

    def list(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            data = response.data
            count = data.get('count') if isinstance(data, dict) else len(data)

            logger.info(
                f"SUCCESS: Retrieved {count} files for user={request.user.id}")
            return response

        except Exception as e:
            logger.exception(
                f"CRITICAL: Database failure fetching files for user={request.user.id}")
            raise e

class RetrieveUpdateDestroyFileView(
    generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'file_id'

    def get_queryset(self):  # type: ignore
        file_id = self.kwargs.get("file_id")
        logger.info(
            f"START: Attemptiong to retrieve file={file_id}"
        )
        if self.request.method in ['GET']:
            # Allow owner or shared users to view
            return File.objects.filter(
                Q(owner=self.request.user) | Q(
                    shares__shared_to=self.request.user)
            ).distinct().select_related("owner").prefetch_related("shares")
        else:
            # Only owner can update/delete
            return File.objects.filter(owner=self.request.user).select_related("owner")

    def retrieve(self, request, *args, **kwargs):
        file_id = kwargs.get("file_id")
        try:
            response = super().retrieve(request, *args, **kwargs)
            logger.info(
                f"SUCCESS: File={file_id} has been retieved"
            )
            return response
        except Exception as e:
            logger.exception(
                f"CRITICAL: Database error retrieving file={file_id}"
            )
            raise e

    def perform_update(self, serializer):
        try:
            instance = serializer.save()
            logger.info(
                f"SUCCESS: File={instance.id} was updated by user={self.request.user.id}")
        except Exception as e:
            logger.exception(
                f"CRITICAL: Update failed for file={self.kwargs.get('file_id')}")
            raise e

    def perform_destroy(self, instance: File):
        try:
            with transaction.atomic():
                instance.shares.all().delete()  # type: ignore
                instance.delete()
            logger.info(
                f"SUCCESS: File={instance.id} was successfully deleted")
        except Exception as e:
            logger.exception(
                f"CRITICAL: Database error in deleting file={instance.id}"
            )


class SharedFilesListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileSerializer

    def get_queryset(self):  # type: ignore
        return (
            File.objects
            .filter(shares__shared_to=self.request.user)
            .select_related("owner")
            .prefetch_related("shares")
            .distinct()
        )

    def list(self, request, *args, **kwargs):
        user = self.request.user
        try:
            response = super().list(request, *args, **kwargs)
            data = response.data
            count = data.get('count') if isinstance(data, dict) else len(data)
            logger.info(
                f"SUCCESS: Listed {count} file(s) shared to user={user.id}")
            return response
        except Exception as e:
            logger.exception(
                f"CRITICAL: Database failed to retrieve files shared to user={user.id}"
            )
            raise e


class UnshareFileDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'file_share_id'
    queryset = FileShare.objects.all()

    def get_object(self) -> FileShare:  # type: ignore
        obj: FileShare = super().get_object()
        if obj.shared_by != self.request.user:
            logger.warning(
                f"SECURITY: User={self.request.user.id} tried to unshare file_share={obj.id} "
                f"owned by user={obj.shared_by.id}"
            )
            raise exceptions.PermissionDenied(
                "You are not authorized to unshare this file."
            )
        return obj

    def delete(self, request, *args, **kwargs):
        file_share_instance = self.get_object()
        file_id = file_share_instance.file.id
        shared_to_user = file_share_instance.shared_to.id
        shared_by_user = file_share_instance.shared_by.id
        try:
            response = super().delete(request, *args, **kwargs)
            logger.info(
                f"SUCCESS: File share instance {file_share_instance.id} where file={file_id} shared to user={shared_to_user} by user={shared_by_user} deleted"
            )
            return response
        except Exception as e:
            logger.exception(
                f"CRITICAL: Database error in deleting file share instance={file_share_instance.id} shared to user={shared_to_user} by user={shared_by_user}"
            )
            raise e


logger = logging.getLogger(__name__)


class DownloadFileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"
    lookup_url_kwarg = "file_id"

    def get_queryset(self):  # type: ignore
        user = self.request.user
        file_id = self.kwargs.get("file_id")

        logger.info(
            f"START: Download request for file={file_id} by user={user.id}")

        return (
            File.objects
            .select_related("owner")
            .filter(
                Q(owner=user) |
                Q(shares__shared_to=user)
            )
            .distinct()
        )

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        try:
            file_obj = self.get_object()
            logger.info(
                f"SUCCESS: Initiating download for file={file_obj.id} '{file_obj.name}' "
                f"({file_obj.size} bytes) for user={user.id}"
            )
            return FileResponse(
                file_obj.file.open("rb"),
                as_attachment=True,
                filename=file_obj.name
            )

        except Exception as e:
            logger.exception(
                f"CRITICAL: Failed to serve file download {kwargs.get('file_id')} "
                f"for user {user.id}"
            )
            raise e
