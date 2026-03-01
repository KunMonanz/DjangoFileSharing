from django.contrib.auth.password_validation import validate_password
from django.contrib.humanize.templatetags.humanize import naturaltime

from rest_framework import serializers

from .models import User, FriendshipRelationship

from file_share.apps.notification.factory import NotificationFactory
from file_share.apps.notification.models import Notification

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        return token


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email"
        ]


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()

        notification_factory = NotificationFactory()
        notification_factory.create_notification(
            recipient=user,
            message_type=Notification.NotificationType.USER_REGISTRATION
        )
        return user


class MiniUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "username",
        ]


class FriendRequestsSerializer(serializers.ModelSerializer):
    sender = MiniUserSerializer(read_only=True)
    reciever = MiniUserSerializer(read_only=True)
    created = serializers.SerializerMethodField(read_only=True)
    updated = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FriendshipRelationship
        fields = [
            'id',
            'sender',
            'reciever',
            'is_accepted',
            'created',
            'updated'
        ]

    def get_created(
        self,
        friendship_relationship: FriendshipRelationship
    ):
        return naturaltime(friendship_relationship.created)

    def get_updated(
        self,
        friendship_relationship: FriendshipRelationship
    ):
        return naturaltime(friendship_relationship.updated)
