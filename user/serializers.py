from django.core.mail import send_mail
from django.utils.encoding import (
    DjangoUnicodeDecodeError,
    force_bytes,
    force_str,
    smart_bytes,
)
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, validators=[
                                   UniqueValidator(queryset=User.objects.all())])
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        field = ['email', 'password']

    def create(self, validated_data):
        print(validated_data)
        email = validated_data['email']
        validated_data['username'] = email
        return User.objects.create_user(**validated_data)


class ResetPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        field = ["email"]

    def validate(self, attrs):
        email = attrs.get("email", "")
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            email_body = f"Hi, You're receiving this email because you requested a password reset for your user account at the drawio plugin. Please copy the following secret key and paste in the corresponding form: \n\n{uidb64}/{token} \n\nThanks for using our site!\n\nYue Chen"
            send_mail(
                "Verfiy your email",
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
        else:
            raise serializers.ValidationError(
                "This email does not exist, please sign up."
            )

        return super().validate(attrs)


class ResetPasswordConfirmSerializer(serializers.Serializer):
    secret_key = serializers.CharField(write_only=True)
    password = serializers.CharField(validators=[validate_password])

    class Meta:
        field = ["secret_key", "password"]

    def validate(self, attrs):
        try:
            secret_key = attrs.get("secret_key")
            password = attrs.get("password")
            uid64, token = secret_key.split("/")
            id = force_str(urlsafe_base64_decode(uid64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed(
                    "Secret key is not valid, please request a new one.", 401
                )
            user.set_password(password)
            user.save()
        except Exception as e:
            raise AuthenticationFailed(
                "Secret key is not valid, please request a new one.", 401
            )

        return super().validate(attrs)
