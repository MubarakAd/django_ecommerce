# serializers.py
from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=255, read_only=True)
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    email = serializers.EmailField(max_length=68, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email',)

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Validate that the provided passwords match and meet your criteria.
        """
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match")

        # Add any additional password validation logic here, such as minimum length requirements.

        return data

    def save(self, **kwargs):
        """
        Set the new password for the user.
        """
        user = self.context['user']
        print("user:    ", user.email,"\n")
        if user:
            # Set the new password
            user.set_password(self.validated_data['password'])
            user.save()

    class Meta:
        model = User
        fields = ('password', 'confirm_password')

class EmailVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=555)

    class Meta:
        model = User
        fields = ['token']
