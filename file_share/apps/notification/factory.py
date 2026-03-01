from .models import Notification
from file_share.apps.account.models import User


class NotificationFactory:
    TEMPLATES = {
        Notification.NotificationType.USER_REGISTRATION: lambda r, a: f"Dear {r.username}, Welcome to Django File Share, we are glad to meet you.",
        Notification.NotificationType.FRIENDSHIP_REQUEST_SENT: lambda r, a: f"Friend request sent to {a.username}.",
        Notification.NotificationType.FRIENDSHIP_REQUEST_ACCEPTED: lambda r, a: f"Friend request from {a.username} has been accepted.",
        Notification.NotificationType.FRIENDSHIP_REQUEST_RECIEVED: lambda r, a: f"Friend request from {a.username}"
    }

    def create_notification(
        self,
        recipient: User,
        message_type: Notification.NotificationType,
        activator: User | None = None
    ) -> Notification:

        if message_type in [
            Notification.NotificationType.FRIENDSHIP_REQUEST_SENT,
            Notification.NotificationType.FRIENDSHIP_REQUEST_ACCEPTED,
            Notification.NotificationType.FRIENDSHIP_REQUEST_RECIEVED
        ] and activator is None:
            raise ValueError(
                f"An activator is required for message type: {message_type}")

        template_func = self.TEMPLATES.get(message_type)
        if not template_func:
            raise ValueError(f"Invalid message type: {message_type}")

        message = template_func(recipient, activator)

        return Notification.objects.create(
            user=recipient,
            message=message,
            message_type=message_type
        )
