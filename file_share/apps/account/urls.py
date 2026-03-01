from django.urls import path
from file_share.apps.account.views import *

urlpatterns = [
    path("",
         RegisterUserView.as_view(),
         name="register-user"
         ),
    path(
        'login/',
        MyTokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),

    # Friendship relation handling
    path(
        'friends/',
        GetAllFriendsView.as_view(),
        name="get-all-friends"
    ),
    path(
        'friends/<uuid:reciever_id>/request/',
        SendFriendRequest.as_view(),
        name="send-friend-request"
    ),
    path(
        'friends/<uuid:reciever_id>/delete/',
        RemoveFriendRequest.as_view(),
        name="delet-friend-request"
    ),
    path(
        'friends/<uuid:friend_request_id>/accept/',
        AcceptFriendRequest.as_view(),
        name="accept-friend-request"
    )
]
