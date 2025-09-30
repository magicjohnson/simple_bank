from django.urls import path
from .views import RegisterView, LoginView, BalanceView, TransactionListView, TransferView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('balance/', BalanceView.as_view(), name='balance'),
    path('transactions/', TransactionListView.as_view(), name='transactions'),
    path('transfer/', TransferView.as_view(), name='transfer'),

]
