from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

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
            balance = BankService.get_balance(request.user)
            return Response({'balance': balance}, status=status.HTTP_200_OK)
        except BankServiceException as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
