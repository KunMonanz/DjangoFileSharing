from django.db.models import Q
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from rest_framework import generics, permissions, exceptions
from rest_framework.parsers import MultiPartParser, FormParser

from .models import File, FileShare

from .serializers import (
    FileSerializer,
    FileUploadSerializer,
    FileShareSerializer
)


User = get_user_model()


class UploadFileCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileUploadSerializer
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        uploaded_file = self.request.FILES.get('file')

        if uploaded_file is not None:
            serializer.save(
                owner=self.request.user,
                name=uploaded_file.name,
                size=uploaded_file.size,
                content_type=uploaded_file.content_type
            )
        else:
            raise exceptions.ValidationError(
                "File must be included for upload"
            )


class ShareFileCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileShareSerializer

    def perform_create(self, serializer):
        file_id = self.kwargs.get('file_id')
        shared_to_id = self.kwargs.get('user_id')

        file = get_object_or_404(File, id=file_id)
        shared_to_user = get_object_or_404(User, id=shared_to_id)

        if file.owner != self.request.user:
            raise ValidationError(
                "You cannot share this file."
            )

        serializer.save(
            shared_by=self.request.user,
            shared_to=shared_to_user,
            file=file
        )


class FileListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileSerializer
    queryset = File.objects.all()

    def get_queryset(self):  # type: ignore
        return (
            File.objects
            .select_related("owner")
            .filter(
                Q(owner=self.request.user) |
                Q(shares__shared_to=self.request.user)
            )
            .distinct()
        )


class RetrieveUpdateDestroyFileView(
    generics.RetrieveUpdateDestroyAPIView
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'file_id'

    def get_queryset(self):  # type: ignore
        if self.request.method in ['GET']:
            # Allow owner or shared users to view
            return File.objects.filter(
                Q(owner=self.request.user) | Q(
                    shares__shared_to=self.request.user)
            ).distinct().select_related("owner").prefetch_related("shares")
        else:
            # Only owner can update/delete
            return File.objects.filter(owner=self.request.user).select_related("owner")

    def perform_destroy(self, instance: File):
        instance.shares.all().delete()
        instance.delete()

class SharedFilesListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileSerializer

    def get_queryset(self):
        return (
            File.objects
            .filter(shares__shared_to=self.request.user)
            .select_related("owner")
            .prefetch_related("shares")
            .distinct()
        )


class UnshareFileDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'file_share_id'
    queryset = FileShare.objects.all()

    def get_object(self) -> FileShare:  # type: ignore
        obj: FileShare = super().get_object()
        if obj.shared_by != self.request.user:
            raise exceptions.PermissionDenied(
                "You are not authorized to unshare this file.")
        return obj
