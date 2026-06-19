"""
Serializers for auth endpoints.

RegisterSerializer  — validates registration input and creates a user
LoginSerializer     — validates login credentials and returns JWT tokens
"""

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser


class RegisterSerializer(serializers.Serializer):
    """
    Validates registration input.
    - email must be a valid email address
    - password must be at least 8 characters
    - raises HTTP 409 (handled in the view) if email already exists
    """

    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        min_length=8,
        write_only=True,
        style={'input_type': 'password'},
        error_messages={
            'min_length': 'Password must be at least 8 characters.',
        },
    )

    def validate_email(self, value):
        """Normalise to lowercase so comparisons are case-insensitive."""
        return value.lower()

    def create(self, validated_data):
        """Create and return a new CustomUser."""
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user

    @staticmethod
    def get_tokens(user):
        """Generate a fresh access/refresh token pair for the given user."""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class LoginSerializer(serializers.Serializer):
    """
    Validates login credentials.
    Returns token pair on success; raises ValidationError on failure.
    """

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate(self, data):
        email = data.get('email', '').lower()
        password = data.get('password', '')

        # Django's authenticate() uses the USERNAME_FIELD (email) under the hood
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password,
        )

        if user is None:
            # Use a non-field error so the view can return a clean 401
            raise serializers.ValidationError(
                {'non_field_errors': 'INVALID_CREDENTIALS'},
                code='INVALID_CREDENTIALS',
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {'non_field_errors': 'INVALID_CREDENTIALS'},
                code='INVALID_CREDENTIALS',
            )

        data['user'] = user
        return data
