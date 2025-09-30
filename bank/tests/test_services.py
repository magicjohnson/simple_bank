from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from bank.models import BankAccount
from bank.services import UserService, UserServiceException, BankService, BankServiceException
from decimal import Decimal


class UserServiceTests(TestCase):
    def setUp(self):
        self.email = "test@example.com"
        self.password = "testpassword123"

    def test_when_missing_email_should_raise_exception(self):
        with self.assertRaises(UserServiceException) as cm:
            UserService.register("", self.password)
        self.assertEqual(str(cm.exception), "Email and password are required")

    def test_when_missing_password_should_raise_exception(self):
        with self.assertRaises(UserServiceException) as cm:
            UserService.register(self.email, "")
        self.assertEqual(str(cm.exception), "Email and password are required")

    def test_when_email_exists_should_raise_exception(self):
        User.objects.create_user(username=self.email, email=self.email, password=self.password)
        with self.assertRaises(UserServiceException) as cm:
            UserService.register(self.email, self.password)
        self.assertEqual(str(cm.exception), "Email already exists")

    def test_when_valid_input_should_create_user_and_account(self):
        user = UserService.register(self.email, self.password)
        account = BankAccount.objects.get(user=user)
        self.assertEqual(user.email, self.email)
        self.assertEqual(len(account.account_number), 10)
        self.assertEqual(account.balance, Decimal("10000.00"))
        self.assertFalse(Token.objects.filter(user=user).exists())

    def test_when_invalid_credentials_should_raise_exception(self):
        User.objects.create_user(username=self.email, email=self.email, password=self.password)
        with self.assertRaises(UserServiceException) as cm:
            UserService.login(self.email, "wrongpassword")
        self.assertEqual(str(cm.exception), "Invalid credentials")

    def test_when_valid_credentials_should_return_token(self):
        User.objects.create_user(username=self.email, email=self.email, password=self.password)
        token = UserService.login(self.email, self.password)
        self.assertEqual(Token.objects.get(user__email=self.email), token)


class BankServiceTests(TestCase):
    def setUp(self):
        self.email = "test@example.com"
        self.password = "testpassword123"
        self.user = UserService.register(self.email, self.password)
        self.account = BankAccount.objects.get(user=self.user)

    def test_generate_account_number_should_return_10_digit_number(self):
        account_number = BankService.generate_account_number()
        self.assertEqual(len(account_number), 10)
        self.assertTrue(account_number.isdigit(), "Account number must be numeric")

    def test_when_no_account_should_raise_exception(self):
        self.account.delete()
        with self.assertRaises(BankServiceException) as cm:
            BankService.get_balance(self.user)
        self.assertEqual(str(cm.exception), "Bank account not found")

    def test_when_account_exists_should_return_balance(self):
        balance = BankService.get_balance(self.user)
        self.assertEqual(balance, Decimal("10000.00"))
