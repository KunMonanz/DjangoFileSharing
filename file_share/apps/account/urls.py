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
]
