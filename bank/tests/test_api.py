from decimal import Decimal
from datetime import timezone as datetime_timezone
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.utils import timezone

from bank.models import BankAccount, Transaction
from bank.services import UserService


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


class BalanceViewTests(APITestCase):
    def setUp(self):
        self.email = "test@example.com"
        self.password = "testpassword123"
        self.balance_url = "/api/balance/"
        self.user = UserService.register(self.email, self.password)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_when_unauthenticated_should_return_401(self):
        self.client.credentials()  # Remove auth
        response = self.client.get(self.balance_url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "Authentication credentials were not provided.")

    def test_when_authenticated_should_return_balance(self):
        response = self.client.get(self.balance_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"balance": Decimal("10000.00")})


class TransactionListViewTests(APITestCase):
    def setUp(self):
        self.email = "test@example.com"
        self.password = "testpassword123"
        self.transactions_url = "/api/transactions/"
        self.user = UserService.register(self.email, self.password)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.account = BankAccount.objects.get(user=self.user)

    def test_when_unauthenticated_should_return_401(self):
        self.client.credentials()  # Remove auth
        response = self.client.get(self.transactions_url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "Authentication credentials were not provided.")

    def test_when_no_transactions_should_return_empty_list(self):
        response = self.client.get(self.transactions_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"transactions": []})

    def test_when_transactions_exist_should_return_list(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal("500.00"),
            transaction_type="credit"
        )
        transaction.created_at = timezone.datetime(2025, 9, 30, 12, 0, 0, tzinfo=datetime_timezone.utc)
        transaction.save()
        response = self.client.get(self.transactions_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["transactions"]), 1)
        self.assertEqual(response.data["transactions"][0]["amount"], "500.00")
        self.assertEqual(response.data["transactions"][0]["transaction_type"], "credit")
        self.assertEqual(response.data["transactions"][0]["created_at"], "2025-09-30T12:00:00Z")

    def test_when_date_range_filter_should_return_filtered_transactions(self):
        transaction1 = Transaction.objects.create(
            account=self.account,
            amount=Decimal("500.00"),
            transaction_type="credit"
        )
        transaction1.created_at = timezone.datetime(2025, 9, 1, 12, 0, 0, tzinfo=datetime_timezone.utc)
        transaction1.save()

        transaction2 = Transaction.objects.create(
            account=self.account,
            amount=Decimal("200.00"),
            transaction_type="debit"
        )
        transaction2.created_at = timezone.datetime(2025, 10, 1, 12, 0, 0, tzinfo=datetime_timezone.utc)
        transaction2.save()

        response = self.client.get(
            self.transactions_url,
            {"date_from": "2025-09-01T00:00:00Z", "date_to": "2025-09-30T23:59:59Z"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["transactions"]), 1)
        self.assertEqual(response.data["transactions"][0]["amount"], "500.00")
        self.assertEqual(response.data["transactions"][0]["transaction_type"], "credit")
        self.assertEqual(response.data["transactions"][0]["created_at"], "2025-09-01T12:00:00Z")

    def test_when_invalid_date_format_should_return_400(self):
        response = self.client.get(self.transactions_url, {"date_from": "invalid_date"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("date_from", response.data)
