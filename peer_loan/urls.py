from django.urls import path
from . import views

urlpatterns = [
    # Loan management endpoints
    path('loan/', views.LoanListCreateView.as_view(), name='loan_list_create'),
    path('loan/<int:pk>/', views.LoanRetrieveDelete.as_view(), name='loan_retrieve_delete'),
    path('loan/transaction/', views.LoanTransactionListCreateView.as_view(), name='loan_transaction_list_create'),
    path('loan/transaction/<int:pk>/', views.LoanTransactionRetrieveDelete.as_view(), name='loan_transaction_retrieve_delete'),
]
