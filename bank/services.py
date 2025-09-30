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
    @staticmethod
    def generate_account_number():
        while True:
            account_number = ''.join([str(random.randint(0, 9)) for _ in range(10)])
            if not BankAccount.objects.filter(account_number=account_number).exists():
                return account_number

    @staticmethod
    def get_balance(user):
        try:
            account = BankAccount.objects.get(user=user)
            return account.balance
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
