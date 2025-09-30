import random
from decimal import Decimal

from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework.authtoken.admin import User
from rest_framework.authtoken.models import Token

from bank.models import BankAccount, Transaction


class UserServiceException(Exception):
    pass


class BankServiceException(Exception):
    pass


class UserService:
    @staticmethod
    @transaction.atomic
    def register(email, password):
        if not email or not password:
            raise UserServiceException('Email and password are required')
        if User.objects.filter(email=email).exists():
            raise UserServiceException('Email already exists')

        user = User.objects.create_user(username=email, email=email, password=password)
        account_number = BankService.generate_account_number()
        BankAccount.objects.create(
            user=user,
            account_number=account_number,
            balance=Decimal('10000.00')
        )
        return user

    @staticmethod
    def login(email, password):
        user = authenticate(username=email, password=password)
        if not user:
            raise UserServiceException('Invalid credentials')

        token, _ = Token.objects.get_or_create(user=user)
        return token


class BankService:
    MIN_FEE = Decimal('5.00')
    FEE_RATE = Decimal('0.025')

    @staticmethod
    def generate_account_number():
        while True:
            account_number = ''.join([str(random.randint(0, 9)) for _ in range(10)])
            if not BankAccount.objects.filter(account_number=account_number).exists():
                return account_number

    @staticmethod
    def get_account(user):
        try:
            account = BankAccount.objects.get(user=user)
            return account
        except BankAccount.DoesNotExist:
            raise BankServiceException('Bank account not found')

    @staticmethod
    def get_transactions(user, date_from=None, date_to=None):
        try:
            filters = {'account__user': user}
            if date_from:
                filters['created_at__gte'] = date_from
            if date_to:
                filters['created_at__lte'] = date_to
            return Transaction.objects.select_related('account').filter(**filters)
        except BankAccount.DoesNotExist:
            raise BankServiceException('Bank account not found')

    @classmethod
    @transaction.atomic
    def transfer(cls, sender, receiver_account_number, amount):
        if amount <= 0:
            raise BankServiceException('Amount must be positive')

        try:
            sender_account = BankAccount.objects.select_for_update().get(user=sender)
            receiver_account = BankAccount.objects.select_for_update().get(account_number=receiver_account_number)
        except BankAccount.DoesNotExist:
            raise BankServiceException('Sender or receiver account not found')

        fee = cls.get_fee(amount)
        total_deduction = amount + fee

        if sender_account.balance < total_deduction:
            raise BankServiceException('Insufficient funds')

        sender_account.balance -= total_deduction
        receiver_account.balance += amount
        sender_account.save()
        receiver_account.save()

        Transaction.objects.create(
            account=sender_account,
            amount=total_deduction,
            transaction_type='debit'
        )
        Transaction.objects.create(
            account=receiver_account,
            amount=amount,
            transaction_type='credit'
        )

    @staticmethod
    def get_fee(amount):
        return max(BankService.MIN_FEE, amount * BankService.FEE_RATE)

