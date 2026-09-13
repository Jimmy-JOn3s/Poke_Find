from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id", "username", "email", "display_name", "role",
            "preferred_language", "preferred_currency", "avatar", "location",
            "bio", "is_verified_seller", "date_joined",
        )
        read_only_fields = ("id", "username", "email", "is_verified_seller", "date_joined")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "username", "email", "password", "display_name", "role",
            "preferred_language", "preferred_currency",
        )

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        identifier = attrs.get(self.username_field, "")
        if "@" in identifier:
            match = User.objects.filter(email__iexact=identifier).only("username").first()
            if match:
                attrs[self.username_field] = match.username
        return super().validate(attrs)
