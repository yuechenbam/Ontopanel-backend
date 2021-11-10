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


class RegisterUser(APIView):
    serializers_class = RegisterSerializer

    def post(self, request):
        user_count = User.objects.all().count()
        if user_count > 100:
            raise APIException(
                'The number of users exceeds 100, sorry, you can no longer register.')

        serializer = self.serializers_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': 'Registerion success, you can login now!'}, status=status.HTTP_201_CREATED)


class LoginUser(ObtainAuthToken):
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


class PasswordResetEmail(APIView):
    serializer_class = ResetPasswordEmailSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)
        return Response({'success': 'Email sent, please check!'}, status=status.HTTP_200_OK)


class PasswordResetConfirm(APIView):
    serializer_class = ResetPasswordConfirmSerializer

    def patch(self, request):

        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)
        return Response({'success': 'Password reset success!'}, status=status.HTTP_200_OK)
