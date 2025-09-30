from datetime import timezone as datetime_timezone
from decimal import Decimal

from django.utils import timezone
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from bank.models import BankAccount, Transaction
from bank.services import UserService, UserServiceException, BankService, BankServiceException


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

    def test_when_no_transactions_should_return_empty_queryset(self):
        transactions = BankService.get_transactions(self.user)
        self.assertEqual(transactions.count(), 0)

    def test_when_transactions_exist_should_return_queryset(self):
        transaction = Transaction.objects.create(
            account=self.account,
            amount=Decimal("500.00"),
            transaction_type="credit"
        )
        transaction.created_at = timezone.datetime(2025, 9, 30, 12, 0, 0, tzinfo=datetime_timezone.utc)
        transaction.save()
        transactions = BankService.get_transactions(self.user)
        self.assertEqual(transactions.count(), 1)
        transaction = transactions.first()
        self.assertEqual(transaction.amount, Decimal("500.00"))
        self.assertEqual(transaction.transaction_type, "credit")
        self.assertEqual(transaction.created_at, timezone.datetime(2025, 9, 30, 12, 0, 0, tzinfo=datetime_timezone.utc))

    def test_when_date_range_filter_should_return_filtered_queryset(self):
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

        transactions = BankService.get_transactions(
            self.user,
            date_from=timezone.datetime(2025, 9, 1, 0, 0, 0, tzinfo=datetime_timezone.utc),
            date_to=timezone.datetime(2025, 9, 30, 23, 59, 59, tzinfo=datetime_timezone.utc)
        )
        self.assertEqual(transactions.count(), 1)
        transaction = transactions.first()
        self.assertEqual(transaction.amount, Decimal("500.00"))
        self.assertEqual(transaction.transaction_type, "credit")
