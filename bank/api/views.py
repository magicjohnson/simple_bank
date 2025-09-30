from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from bank.api.serializers import TransactionQuerySerializer, TransactionSerializer, TransferSerializer
from bank.services import UserService, UserServiceException, BankService, BankServiceException


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            UserService.register(email, password)
            return Response(status=status.HTTP_201_CREATED)
        except UserServiceException as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            token = UserService.login(email, password)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        except UserServiceException as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BalanceView(APIView):
    def get(self, request):
        try:
            account = BankService.get_account(request.user)
            data = {
                'balance': account.balance,
                "account_number": account.account_number
            }
            return Response(data, status=status.HTTP_200_OK)
        except BankServiceException as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TransactionListView(APIView):
    def get(self, request):
        try:
            serializer = TransactionQuerySerializer(data=request.query_params)
            serializer.is_valid(raise_exception=True)
            date_from = serializer.validated_data.get('date_from')
            date_to = serializer.validated_data.get('date_to')
            transactions = BankService.get_transactions(request.user, date_from, date_to)
            serialized_transactions = TransactionSerializer(transactions, many=True).data
            return Response({'transactions': serialized_transactions}, status=status.HTTP_200_OK)
        except BankServiceException as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TransferView(APIView):
    def post(self, request):
        try:
            serializer = TransferSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            BankService.transfer(
                sender=request.user,
                receiver_account_number=serializer.validated_data['receiver_account_number'],
                amount=serializer.validated_data['amount']
            )
            return Response({'message': 'Transfer successful'}, status=status.HTTP_200_OK)
        except BankServiceException as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
