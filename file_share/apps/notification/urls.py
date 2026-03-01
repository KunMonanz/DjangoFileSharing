from django.urls import path
from file_share.apps.notification.views import *

urlpatterns = [
    path(
        '',
        NotificationListView.as_view(),
        name="get-all-notifications"
    ),
    path(
        '<uuid:notification_id>',
        RetrieveNotification.as_view(),
        name="retrieve-notification"
    )
]
