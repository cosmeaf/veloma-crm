from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import OtpCode, ResetPasswordToken, LoginAttempt
from services.utils.auth.constants import LOGIN_MAX_ATTEMPTS

User = get_user_model()

class AuthenticationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('auth-register-list')
        self.login_url = reverse('auth-login-list')
        self.recovery_url = reverse('auth-recovery-list')
        self.otp_verify_url = reverse('auth-otp-verify-list')
        self.reset_password_url = reverse('auth-reset-password-list')

        self.user_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": "testpassword123",
            "password2": "testpassword123"
        }
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="testpassword123"
        )

    def test_user_registration(self):
        data = {
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "password2": "newpassword123"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_user_login_success(self):
        data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['email'], "test@example.com")

    def test_user_login_failure(self):
        data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify login attempt recorded
        self.assertTrue(LoginAttempt.objects.filter(email="test@example.com", success=False).exists())

    def test_brute_force_protection(self):
        data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }

        # Perform failures up to the limit
        for _ in range(LOGIN_MAX_ATTEMPTS):
            self.client.post(self.login_url, data)

        # The next attempt should be blocked
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Muitas tentativas", str(response.data))

    def test_password_recovery_flow(self):
        # 1. Request recovery
        response = self.client.post(self.recovery_url, {"email": "test@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        otp = OtpCode.objects.filter(user=self.user).first()
        self.assertIsNotNone(otp)

        # 2. Verify OTP
        verify_data = {
            "email": "test@example.com",
            "code": otp.code
        }
        response = self.client.post(self.otp_verify_url, verify_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('reset_token', response.data)
        reset_token = response.data['reset_token']

        # 3. Reset password
        reset_data = {
            "token": reset_token,
            "password": "newpassword456",
            "password2": "newpassword456"
        }
        response = self.client.post(self.reset_password_url, reset_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. Verify new password works
        # self.assertTrue(self.user.check_password("testpassword123")) # Old password still in memory instance
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword456"))
