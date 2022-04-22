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
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class RegisterUser(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary='user registrationn',
        operation_description='User registration in Ontopanel-EntityManager.',
        request_body=RegisterSerializer,
        responses={
            '200': "Registerion success, you can login now!",
            "400": "Bad Request",
            '503': 'The number of users exceeds 100, sorry, you can no longer register.'
        },
        security=[],
    )
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

    @swagger_auto_schema(
        operation_summary='user login',
        operation_description='User login in Ontopanel-EntityManager. username == email.',
        responses={
            "200": openapi.Response('response description', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                "token": openapi.Schema(type=openapi.TYPE_STRING, description="generated token"),
                "user_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                "email": openapi.Schema(type=openapi.TYPE_STRING),
            }),
                examples={
                "application/json": {
                    'token': "<Token>",
                    'user_id': 1,
                    'email': "test@mail.com"
                }

            }),
            "400": "Bad Request",
        },
    )
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

    @swagger_auto_schema(
        operation_summary='user logout',
        operation_description='User logout in Ontopanel-EntityManager.',
        responses={
            '200': "You have successfully logged out.",
        })
    def get(self, request):

        request.user.auth_token.delete()
        data = {
            "message": "You have successfully logged out.",
        }
        return Response(data, status=status.HTTP_200_OK)


class PasswordResetEmail(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary='reset password',
        operation_description='User reset password in Ontopanel-EntityManager. The backend sends secrect key by email.',
        request_body=ResetPasswordEmailSerializer,
        responses={
            '200': "Email sent, please check!",
            "400": "This email does not exist, please sign up.",
        },
        security=[],
    )
    def post(self, request):
        serializer = ResetPasswordEmailSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        return Response({'success': 'Email sent, please check!'}, status=status.HTTP_200_OK)


class PasswordResetConfirm(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary='reset password confirm',
        operation_description='User reset password with secrect key in Ontopanel-EntityManager.',
        request_body=ResetPasswordConfirmSerializer,
        responses={
            '200': "Password reset success!",
            "401": "Secret key is not valid, please request a new one.",
        },
    )
    def patch(self, request):

        serializer = ResetPasswordConfirmSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        return Response({'success': 'Password reset success!'}, status=status.HTTP_200_OK)
