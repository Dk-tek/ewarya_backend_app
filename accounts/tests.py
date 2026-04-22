from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class SessionTokenTests(APITestCase):
    def test_register_creates_staff_console_user(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'new_admin',
                'password': 'secret123',
                'phone_number': '9000000000',
                'email': 'new-admin@example.com',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.get(username='new_admin').is_staff)
        self.assertIn('access', response.data['tokens'])

    def test_register_duplicate_phone_returns_validation_error(self):
        User.objects.create_user(
            username='existing_admin',
            password='secret123',
            phone_number='9000000004',
            email='existing-admin@example.com',
            is_staff=True,
        )

        response = self.client.post(
            reverse('register'),
            {
                'username': 'second_admin',
                'password': 'secret123',
                'phone_number': '9000000004',
                'email': 'second-admin@example.com',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)

    def test_authenticated_django_session_can_receive_jwt_tokens(self):
        user = User.objects.create_user(
            username='admin_user',
            password='secret123',
            phone_number='9000000001',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse('session-token'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'admin_user')
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

    def test_password_console_login_requires_staff_user(self):
        User.objects.create_user(
            username='plain_user',
            password='secret123',
            phone_number='9000000002',
        )

        response = self.client.post(
            reverse('login-password'),
            {'username': 'plain_user', 'password': 'secret123'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_password_console_login_accepts_staff_user(self):
        User.objects.create_user(
            username='staff_user',
            password='secret123',
            phone_number='9000000003',
            is_staff=True,
        )

        response = self.client.post(
            reverse('login-password'),
            {'username': 'staff_user', 'password': 'secret123'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data['tokens'])
