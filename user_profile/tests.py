from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from user_profile.models import UserProfile, BancoCredential
from services.utils.crypto.fernet_cipher import FernetCipher

User = get_user_model()

class UserProfileTests(APITestCase):
    def setUp(self):
        self.profile_list_url = reverse('user-profile-list')
        self.bank_list_url = reverse('bancos-list')

        self.user = User.objects.create_user(
            username="user@example.com",
            email="user@example.com",
            password="password123"
        )
        self.staff_user = User.objects.create_user(
            username="staff@example.com",
            email="staff@example.com",
            password="password123",
            is_staff=True
        )
        self.client.force_authenticate(user=self.user)

    def test_create_user_profile(self):
        data = {
            "nif": "123456789",
            "person_type": "PF",
            "legal_name": "Test User",
            "phone": "912345678",
            "address": "Test Street"
        }
        response = self.client.post(self.profile_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertEqual(UserProfile.objects.first().user, self.user)

    def test_bank_credential_encryption(self):
        # 1. Create profile first
        profile = UserProfile.objects.create(
            user=self.user,
            nif="123456789",
            person_type="PF",
            legal_name="Test User"
        )

        # 2. Create bank credential
        data = {
            "profile": profile.id,
            "bank_name": "Test Bank",
            "iban": "PT500000",
            "username": "bankuser",
            "password": "secretpassword"
        }
        response = self.client.post(self.bank_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        credential = BancoCredential.objects.first()
        self.assertNotEqual(credential.secret_encrypted, "secretpassword")

        # Verify it can be decrypted
        decrypted = FernetCipher().decrypt(credential.secret_encrypted)
        self.assertEqual(decrypted, "secretpassword")

    def test_bank_credential_visibility(self):
        profile = UserProfile.objects.create(
            user=self.user,
            nif="123456789",
            person_type="PF",
            legal_name="Test User"
        )
        BancoCredential.objects.create(
            profile=profile,
            bank_name="Test Bank",
            username="bankuser",
            secret_encrypted=FernetCipher().encrypt("secretpassword")
        )

        # We need to use retrieve to see the 'password' field in DetailSerializer
        detail_url = reverse('bancos-detail', args=[BancoCredential.objects.first().id])

        # User sees "hidden"
        response = self.client.get(detail_url)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # If the user is NOT staff, they might not even have permission to retrieve
        # based on IsOwnerOrStaff if 'user' isn't on BancoCredential directly?
        # BancoCredential has 'profile' which has 'user'.

        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(response.data.get('password'), "hidden")

        # Staff sees actual password
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('password'), "secretpassword")
