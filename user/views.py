from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.exceptions import APIException
from .serializers import ResetPasswordEmailSerializer, ResetPasswordConfirmSerializer, RegisterSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated


"""
Authentication system that communicates with Ontopanel-EntityManager in the frontend.
More detailed API documentation is available in the README.
"""


class RegisterUser(APIView):
    permission_classes = [AllowAny]
    """
    User registration. Registered users can save their ontology in the databank.
    """

    def post(self, request):
        user_count = User.objects.all().count()
        if user_count > 100:
            raise APIException(
                'The number of users exceeds 100, sorry, you can no longer register.')

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': 'Registerion success, you can login now!'}, status=status.HTTP_201_CREATED)


class LoginUser(ObtainAuthToken):
    permission_classes = [AllowAny]

    """
    User login. After login in Ontopanel-EntityManager, ontologies saved in the databank is automatically loaded.
    """

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })


class LogoutUser(APIView):

    permission_classes = [IsAuthenticated]

    """
    User logout.
    """

    def get(self, request):

        request.user.auth_token.delete()
        data = {
            "message": "You have successfully logged out.",
        }
        return Response(data, status=status.HTTP_200_OK)


class PasswordResetEmail(APIView):
    permission_classes = [AllowAny]
    """
    User resets the password. After entering the registered email address, the backend email server will send the secret key.
    """

    def post(self, request):
        serializer = ResetPasswordEmailSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        return Response({'success': 'Email sent, please check!'}, status=status.HTTP_200_OK)


class PasswordResetConfirm(APIView):
    permission_classes = [AllowAny]

    """
    User enters secrect key and new password to reset.
    """

    def patch(self, request):

        serializer = ResetPasswordConfirmSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        return Response({'success': 'Password reset success!'}, status=status.HTTP_200_OK)
