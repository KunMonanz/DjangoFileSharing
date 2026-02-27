from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework import generics, permissions

from .serializers import MyTokenObtainPairSerializer, UserRegisterSerializer


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterUserView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]
