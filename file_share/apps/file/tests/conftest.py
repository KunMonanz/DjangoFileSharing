from file_share.apps.file.models import File
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def authenticated_user():
    return User.objects.create_user(
        username="testuser",
        email="test@test.com",
        password="password123"
    )


@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        username="user_a",
        email="a@test.com",
        password="password123"
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        username="user_b",
        email="b@test.com",
        password="password123"
    )


@pytest.fixture
def user_a_file(user_a):
    return File.objects.create(
        owner=user_a,
        name="test.txt",
        size=4,
        content_type="text/plain"
    )


@pytest.fixture
def user_authenticated_file(authenticated_user):
    return File.objects.create(
        owner=authenticated_user,
        name="test.txt",
        size=4,
        content_type="text/plain"
    )
