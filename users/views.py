from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, OTP
from .serializers import (
    RegisterSerializer, LoginSerializer, VerifyOTPSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer
)
import random
from datetime import timedelta


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, code, purpose):
    if purpose == 'verify_email':
        subject = 'StatFort - Verify Your Email'
        message = f'Your StatFort verification code is: {code}\n\nThis code expires in 10 minutes.'
    else:
        subject = 'StatFort - Password Reset Code'
        message = f'Your StatFort password reset code is: {code}\n\nThis code expires in 10 minutes.'

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            code = generate_otp()
            OTP.objects.create(
                user=user,
                code=code,
                purpose='verify_email',
                expires_at=timezone.now() + timedelta(minutes=10),
            )
            send_otp_email(user.email, code, 'verify_email')
            return Response({'message': 'Registration successful. Check your email for your verification code.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            try:
                user = User.objects.get(email=email)
                otp = OTP.objects.filter(user=user, code=code, purpose='verify_email', is_used=False).latest('created_at')
                if otp.is_expired():
                    return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
                otp.is_used = True
                otp.save()
                user.is_active = True
                user.is_verified = True
                user.save()
                return Response({'message': 'Email verified successfully. You can now log in.'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
            except OTP.DoesNotExist:
                return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(request, email=email, password=password)
            if not user:
                return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
            if not user.is_verified:
                return Response({'error': 'Please verify your email before logging in.'}, status=status.HTTP_403_FORBIDDEN)
            token = RefreshToken.for_user(user)
            return Response({
                'message': 'Login successful.',
                'user': {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'is_superuser': user.is_superuser,
                },
                'refresh': str(token),
                'access': str(token.access_token),
            }, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                code = generate_otp()
                OTP.objects.create(
                    user=user,
                    code=code,
                    purpose='reset_password',
                    expires_at=timezone.now() + timedelta(minutes=10),
                )
                send_otp_email(user.email, code, 'reset_password')
                return Response({'message': 'Password reset code sent to your email.'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'No account found with this email.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            new_password = serializer.validated_data['new_password']
            try:
                user = User.objects.get(email=email)
                otp = OTP.objects.filter(user=user, code=code, purpose='reset_password', is_used=False).latest('created_at')
                if otp.is_expired():
                    return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
                otp.is_used = True
                otp.save()
                user.set_password(new_password)
                user.save()
                return Response({'message': 'Password reset successful. You can now log in.'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
            except OTP.DoesNotExist:
                return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
