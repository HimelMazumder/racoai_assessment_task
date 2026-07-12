from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationTest(APITestCase):
    def test_user_registration_success(self):
        """Verify a new user can register with valid data."""
        response = self.client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['email'], 'newuser@example.com')
        self.assertNotIn('password', response.data)

    def test_user_registration_duplicate_email(self):
        """Verify duplicate email returns 400."""
        User.objects.create_user(
            username='existing', email='taken@example.com', password='password123'
        )
        response = self.client.post('/api/auth/register/', {
            'username': 'another',
            'email': 'taken@example.com',
            'password': 'securepass123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_jwt_tokens(self):
        """Verify login returns both access and refresh tokens."""
        User.objects.create_user(
            username='testlogin', email='login@example.com', password='testpass123'
        )
        response = self.client.post('/api/auth/login/', {
            'username': 'testlogin',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_profile_requires_authentication(self):
        """Verify unauthenticated profile access returns 401."""
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
