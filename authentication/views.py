from django.template.loader import render_to_string
from django.urls import reverse
from rest_framework import status, views
from rest_framework.generics import GenericAPIView, CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.authtoken.models import Token
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth import authenticate
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
import jwt
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import User
from .serializers import (EmailVerificationSerializer, LoginSerializer, RegisterSerializer,
    SetPasswordSerializer, UserSerializer)

class RegisterView(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        user = request.data
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_data = serializer.data
        user = User.objects.get(email=user_data['email'])
        email = user.email
        name = f"{user.first_name} {user.last_name}"
        current_site = get_current_site(request)
        email_verification_url = reverse('activate')  # Adjust this to match your URL pattern
        token = RefreshToken.for_user(user).access_token
        absurl = f'http://{current_site}{email_verification_url}?token={str(token)}'

        # Modify your HTML message with dynamic data
        message = render_to_string('activation.html', {
            'full_name': name,
            'urls': absurl,
        })

        # Your inline CSS styles
        inline_styles = """
        <style>
        /* Add your CSS styles here */
        body {
            background-color: #e9ecef;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #ffffff;
        }
        h1 {
            font-size: 32px;
            font-weight: 700;
            color: #666666;
            
        }
        p {
            font-size: 16px;
            line-height: 24px;
            color: #666666;
        }
        a.button {
            display: inline-block;
            background-color: #007bff;
            color: #ffffff;
            padding: 10px 20px;
            text-decoration: none;
        }
        </style>
        """

        # Add the inline CSS styles to the HTML message
        message = f"{inline_styles}{message}"

        email_subject = 'Verify your email'
        to_email = email

        try:
            send_email = EmailMessage(email_subject, message, to=[to_email])
            send_email.content_subtype = 'html'  # Set the content type to HTML
            send_email.send()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Handle email sending errors
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        if not email or not password:
            return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate using email
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Generate a refresh token for the user
            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data
            response_data = {'user': user_data, 'access_token': str(refresh.access_token), 'refresh_token': str(refresh)}
            return Response(response_data)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(CreateAPIView):
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            # Generate a password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Build the reset URL
            current_site = get_current_site(request)
            reset_url = f"http://{current_site.domain}/auth/reset-password/{uid}/{token}/"

            # Send the password reset email
            subject = 'Password Reset'
            message = render_to_string('password_reset_email.html', {
                'reset_url': reset_url,
                'user': user,
            })
            email = EmailMessage(subject, message, to=[email])
            email.content_subtype = 'html'
            email.send()

            return Response({'detail': 'Password reset email sent'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
class SetPasswordView(GenericAPIView):
    serializer_class = SetPasswordSerializer

    def post(self, request, uid, token):
        try:
            # Decode the UID to get the user's primary key
            uid_bytes = urlsafe_base64_decode(uid)
            user_id = str(uid_bytes, encoding='utf-8')
            user = User.objects.get(pk=user_id)

            # Check if the token is valid
            if not default_token_generator.check_token(user, token):
                return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': 'Invalid user or token'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SetPasswordSerializer(data=request.data, context={'user': user})

        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Password changed successfully'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer

    token_param_config = openapi.Parameter(
        'token', in_=openapi.IN_QUERY, description='Description', type=openapi.TYPE_STRING)

    @swagger_auto_schema(manual_parameters=[token_param_config])
    def get(self, request):
        token = request.GET.get('token')
        try:
            print("Received token:", token)  # Debugging: Print the received token
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            print("Decoded token:", decoded_token)  # Debugging: Print the decoded token
            user_id = decoded_token.get('user_id')
            
            if user_id is not None:
                user = User.objects.get(id=user_id)
                if not user.is_active:
                    user.is_active = True
                    user.save()
                    return Response({'email': 'Successfully activated'}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'User is already verified'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Invalid user_id in token'}, status=status.HTTP_400_BAD_REQUEST)
            
        except jwt.ExpiredSignatureError as e:
            print("Expired Signature Error:", e)  # Debugging: Print the exception
            return Response({'error': 'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError as e:
            print("Decode Error:", e)  # Debugging: Print the exception
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist as e:
            print("User Does Not Exist Error:", e)  # Debugging: Print the exception
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
