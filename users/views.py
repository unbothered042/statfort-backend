from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .models import User, OTP
from .serializers import (
    RegisterSerializer, LoginSerializer, VerifyOTPSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer
)
import random
import os
import resend
import requests
from datetime import timedelta


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, code, purpose):
    if purpose == 'verify_email':
        subject = 'StatFort - Verify Your Email'
        message = f'Your StatFort verification code is: <strong>{code}</strong><br><br>This code expires in 10 minutes.'
    else:
        subject = 'StatFort - Password Reset Code'
        message = f'Your StatFort password reset code is: <strong>{code}</strong><br><br>This code expires in 10 minutes.'

    resend.api_key = os.getenv('RESEND_API_KEY')

    try:
        resend.Emails.send({
            "from": "StatFort <onboarding@resend.dev>",
            "to": [email],
            "subject": subject,
            "html": f'<p>{message}</p>'
        })
    except Exception as e:
        print(f"Resend error: {str(e)}")


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = True
            user.is_verified = True
            user.save()
            return Response({'message': 'Registration successful. You can now log in.'}, status=status.HTTP_201_CREATED)
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
                    return Response({'error': 'OTP has expired.'}, status=status.HTTP_400_BAD_REQUEST)
                otp.is_used = True
                otp.save()
                user.is_active = True
                user.is_verified = True
                user.save()
                return Response({'message': 'Email verified successfully.'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
            except OTP.DoesNotExist:
                return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['identifier']
            password = serializer.validated_data['password']

            user = None
            if '@' in identifier:
                user = authenticate(request, email=identifier, password=password)
            else:
                try:
                    user_obj = User.objects.get(username__iexact=identifier)
                    user = authenticate(request, email=user_obj.email, password=password)
                except User.DoesNotExist:
                    pass

            if not user:
                return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
            if not user.is_verified:
                return Response({'error': 'Please verify your email before logging in.'}, status=status.HTTP_403_FORBIDDEN)

            user.reset_daily_limits_if_needed()
            token = RefreshToken.for_user(user)
            is_premium = user.check_premium()
            ai_limit = user.get_ai_limit()

            return Response({
                'message': 'Login successful.',
                'user': {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'username': user.username,
                    'state': user.state,
                    'is_superuser': user.is_superuser,
                    'is_premium': is_premium,
                    'premium_expires_at': user.premium_expires_at,
                    'ai_insight_count': user.ai_insight_count,
                    'elite_insight_count': user.elite_insight_count,
                    'ai_limit': ai_limit,
                    'ai_limit_reset_at': user.ai_limit_reset_at,
                },
                'refresh': str(token),
                'access': str(token.access_token),
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                User.objects.get(email=email)
                return Response({'message': 'Email found. You can now reset your password.'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'No account found with this email.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')

        if not email or not new_password:
            return Response({'error': 'Email and new password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 6:
            return Response({'error': 'Password must be at least 6 characters.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password reset successful.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class InitializePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        paystack_secret = os.getenv('PAYSTACK_SECRET_KEY')
        headers = {
            'Authorization': f'Bearer {paystack_secret}',
            'Content-Type': 'application/json',
        }
        data = {
            'email': user.email,
            'amount': 150000,
            'currency': 'NGN',
            'callback_url': f'{os.getenv("FRONTEND_URL", "https://statfort.vercel.app")}/elite?payment=success',
            'metadata': {'user_id': user.id, 'plan': 'premium_monthly'},
        }
        response = requests.post('https://api.paystack.co/transaction/initialize', json=data, headers=headers)
        result = response.json()

        if result.get('status'):
            return Response({
                'authorization_url': result['data']['authorization_url'],
                'reference': result['data']['reference'],
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Payment initialization failed.'}, status=status.HTTP_400_BAD_REQUEST)


class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        reference = request.data.get('reference')
        if not reference:
            return Response({'error': 'Reference is required.'}, status=status.HTTP_400_BAD_REQUEST)

        paystack_secret = os.getenv('PAYSTACK_SECRET_KEY')
        headers = {'Authorization': f'Bearer {paystack_secret}'}
        response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
        result = response.json()

        if result.get('status') and result['data']['status'] == 'success':
            user = request.user
            user.is_premium = True
            user.premium_expires_at = timezone.now() + timedelta(days=30)
            user.save()
            return Response({
                'message': 'Payment verified. Premium activated for 30 days.',
                'is_premium': True,
                'premium_expires_at': user.premium_expires_at,
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Payment verification failed.'}, status=status.HTTP_400_BAD_REQUEST)


class TestEmailView(APIView):
    def get(self, request):
        try:
            resend.api_key = os.getenv('RESEND_API_KEY')
            response = resend.Emails.send({
                "from": "StatFort <onboarding@resend.dev>",
                "to": ["statfort9@gmail.com"],
                "subject": "StatFort Test",
                "html": "<p>Test email from StatFort server.</p>"
            })
            return Response({'success': True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)