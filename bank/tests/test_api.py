from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from bank.models import BankAccount
from decimal import Decimal


class RegisterViewTests(APITestCase):
    def setUp(self):
        self.email = "test@example.com"
        self.password = "testpassword123"
        self.register_url = "/api/register/"

    def test_when_missing_email_should_return_400(self):
        response = self.client.post(self.register_url, {"password": self.password})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"detail": "Email and password are required"})

    def test_when_missing_password_should_return_400(self):
        response = self.client.post(self.register_url, {"email": self.email})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"detail": "Email and password are required"})

    def test_when_email_exists_should_return_400(self):
        User.objects.create_user(username=self.email, email=self.email, password=self.password)
        response = self.client.post(self.register_url, {"email": self.email, "password": self.password})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"detail": "Email already exists"})

    def test_when_valid_input_should_create_user_and_account(self):
        new_email = "new@example.com"
        response = self.client.post(self.register_url, {"email": new_email, "password": self.password})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email=new_email).exists())
        user = User.objects.get(email=new_email)
        account = BankAccount.objects.get(user=user)
        self.assertEqual(len(account.account_number), 10)
        self.assertEqual(account.balance, Decimal("10000.00"))
        self.assertFalse(Token.objects.filter(user=user).exists())


class LoginViewTests(APITestCase):
    def setUp(self):
        self.email = "test@example.com"
        self.password = "testpassword123"
        self.login_url = "/api/login/"
        User.objects.create_user(username=self.email, email=self.email, password=self.password)

    def test_when_invalid_credentials_should_return_400(self):
        response = self.client.post(self.login_url, {"email": self.email, "password": "wrongpassword"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"detail": "Invalid credentials"})

    def test_when_valid_credentials_should_return_token(self):
        response = self.client.post(self.login_url, {"email": self.email, "password": self.password})
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        token = Token.objects.get(user__email=self.email)
        self.assertEqual(response.data["token"], token.key)
