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
            BankService.get_account(self.user)
        self.assertEqual(str(cm.exception), "Bank account not found")

    def test_when_account_exists_should_return_balance(self):
        account = BankService.get_account(self.user)
        self.assertEqual(account.balance, Decimal("10000.00"))

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

    def test_get_fee_minimum_fee_applied(self):
        fee = BankService.get_fee(Decimal('100.00'))
        self.assertEqual(fee, Decimal('5.00'))

    def test_get_fee_percentage_fee_applied(self):
        fee = BankService.get_fee(Decimal('300.00'))
        self.assertEqual(fee, Decimal('7.50'))

    def test_get_fee_at_threshold(self):
        fee = BankService.get_fee(Decimal('200.00'))  # 200 * 0.025 = 5.00
        self.assertEqual(fee, Decimal('5.00'))

    def test_get_fee_zero_amount(self):
        fee = BankService.get_fee(Decimal('0.00'))
        self.assertEqual(fee, Decimal('5.00'))

    def test_when_transfer_amount_negative_should_raise_exception(self):
        receiver = UserService.register("receiver@example.com", self.password)
        receiver_account = BankAccount.objects.get(user=receiver)
        with self.assertRaises(BankServiceException) as cm:
            BankService.transfer(self.user, receiver_account.account_number, Decimal("-100.00"))
        self.assertEqual(str(cm.exception), "Amount must be positive")

    def test_when_receiver_account_not_found_should_raise_exception(self):
        with self.assertRaises(BankServiceException) as cm:
            BankService.transfer(self.user, "1234567890", Decimal("100.00"))
        self.assertEqual(str(cm.exception), "Sender or receiver account not found")

    def test_when_insufficient_funds_should_raise_exception(self):
        receiver = UserService.register("receiver@example.com", self.password)
        receiver_account = BankAccount.objects.get(user=receiver)
        self.account.balance = Decimal("10.00")
        self.account.save()
        with self.assertRaises(BankServiceException) as cm:
            BankService.transfer(self.user, receiver_account.account_number, Decimal("100.00"))
        self.assertEqual(str(cm.exception), "Insufficient funds")

    def test_when_valid_transfer_should_update_balances_and_record_transactions(self):
        receiver = UserService.register("receiver@example.com", self.password)
        receiver_account = BankAccount.objects.get(user=receiver)
        initial_sender_balance = self.account.balance
        initial_receiver_balance = receiver_account.balance
        transfer_amount = Decimal("100.00")
        fee = max(Decimal("5.00"), transfer_amount * Decimal("0.025"))

        BankService.transfer(self.user, receiver_account.account_number, transfer_amount)

        self.account.refresh_from_db()
        receiver_account.refresh_from_db()
        self.assertEqual(self.account.balance, initial_sender_balance - transfer_amount - fee)
        self.assertEqual(receiver_account.balance, initial_receiver_balance + transfer_amount)

        sender_transactions = self.account.transactions.all()
        receiver_transactions = receiver_account.transactions.all()
        self.assertEqual(sender_transactions.count(), 1)
        self.assertEqual(receiver_transactions.count(), 1)
        self.assertEqual(sender_transactions[0].amount, transfer_amount + fee)
        self.assertEqual(sender_transactions[0].transaction_type, "debit")
        self.assertEqual(receiver_transactions[0].amount, transfer_amount)
        self.assertEqual(receiver_transactions[0].transaction_type, "credit")
