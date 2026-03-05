from file_share.apps.file.models import File
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
class TestFileUpload:
    client = APIClient()

    def test_if_anonymous_for_upload_file_returns_401(self):
        file = SimpleUploadedFile(
            "test.txt",
            b"hello world",
            content_type="text/plain"
        )

        data = {
            "file": file,
            "name": "Test File"
        }

        response = self.client.post(
            "/api/files/upload/",
            data,
            format="multipart"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_file(self, authenticated_user):

        self.client.force_authenticate(user=authenticated_user)

        file = SimpleUploadedFile(
            "test.txt",
            b"hello world",
            content_type="text/plain"
        )

        data = {
            "file": file,
            "name": "Test File"
        }

        response = self.client.post(
            "/api/files/upload/",
            data,
            format="multipart"
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_upload_without_file_returns_400(self, authenticated_user):
        self.client.force_authenticate(user=authenticated_user)
        response = self.client.post(
            "/api/files/upload/",
            {"name": "Test File"},
            format="multipart"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "file" in response.data

    def test_upload_throttling(self, authenticated_user):
        file = SimpleUploadedFile("test.txt", b"data")
        self.client.force_authenticate(user=authenticated_user)

        for _ in range(10):
            response = self.client.post(
                "/api/files/upload/",
                {"file": file},
                format="multipart"
            )

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
class TestFileList:
    client = APIClient()

    def test_if_user_is_anonymous_for_list_files_returns_401(self):
        response = self.client.get("/api/files/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_file_returns_200(self, authenticated_user):
        self.client.force_authenticate(user=authenticated_user)

        response = self.client.get("/api/files/")

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestShareFile:
    client = APIClient()

    def test_file_share_returns_401_for_anonymous_user(self, user_a_file: File, user_a):

        response = self.client.get(
            f"/api/files/shares/{user_a_file.id}/to/{user_a.id}/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_file_share_only_to_friends(
        self,
        user_authenticated_file,
        authenticated_user,
        user_a
    ):
        self.client.force_authenticate(user=authenticated_user)
        response = self.client.get(
            f"api/files/shares/{user_authenticated_file}/to/{user_a.id}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
