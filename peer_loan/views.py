from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError


from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date
from .models import *
from accounts.models import Contact
from .serializers import *
User = get_user_model()


class LoanListCreateView(generics.ListCreateAPIView):
    """List and create loans"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoanSerializer
    queryset = Loan.objects.all()


    def perform_create(self, serializer):
        """
        Save the loan with the current user as the owner.
        """
        serializer.save(user=self.request.user)


   
   


class LoanTransactionListCreateView(generics.ListCreateAPIView):
    """Create a loan transaction"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoanTransactionSerializer
    

    def get_queryset(self):
        """
        List all transactions for the current user and the given loan_pk.
        """
        user = self.request.user
        loan_id = self.request.query_params.get('loan')
        if loan_id is not None:
            transactions = LoanTransaction.objects.filter( loan_id=loan_id, loan__user=user )
        else:
            transactions = LoanTransaction.objects.filter( loan__user=user )

        transactions = transactions.order_by('-transaction_date')
        return transactions 

    def perform_create(self, serializer):
        """
        Ensure that the loan for which the transaction is being created belongs to the current user.
        Also validate that principal payment is not greater than the outstanding principal.
        """
        user = self.request.user
        loan_id = self.request.data.get('loan')
        try:
            loan = Loan.objects.get(id=loan_id, user=user)
        except Loan.DoesNotExist:
            raise PermissionDenied("You do not have permission to add a transaction to this loan.")

        tx_type = self.request.data.get('type')
        amount = serializer.validated_data.get('amount')
        if tx_type == LoanTransaction.TransactionType.PRINCIPAL_PAYMENT:
            outstanding = loan.get_total_amount()
            if amount > outstanding:
                raise ValidationError(f"Principal payment ({amount}) cannot be greater than outstanding principal ({outstanding}).")

        serializer.save(loan=loan)



class LoanTransactionRetrieveDelete(generics.RetrieveDestroyAPIView):
    """Retrieve and delete a loan transaction"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoanTransactionSerializer
    queryset = LoanTransaction.objects.all()
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        return LoanTransaction.objects.filter(loan__user=user)


class LoanRetrieveDelete(generics.RetrieveDestroyAPIView):
    """
    Retrieve and delete a loan for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoanSerializer
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        return Loan.objects.filter(user=user)


class ContactLoanList(generics.ListAPIView):
    """
    List contacts with total loan amount and total accrued interest for each contact.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Get all contacts for which the user has loans
        user = self.request.user
        return (
            Loan.objects.filter(user=user)
            .values('contact')
            .distinct()
        )

    def list(self, request, *args, **kwargs):
        user = request.user
        # Get all contacts for which the user has loans
        contact_ids = (
            Loan.objects.filter(user=user)
            .values_list('contact', flat=True)
            .distinct()
        )
        contacts = Contact.objects.filter(id__in=contact_ids)
        data = []
        for contact in contacts:
            loans = Loan.objects.filter(user=user, contact=contact, status=Loan.Status.ACTIVE)
            total_amount = sum(loan.outstanding_principal() for loan in loans)
            # Sum up accrued interest for all loans for this contact
            
            total_accrued_interest = sum(
                loan.calculate_outstanding_interest() for loan in loans
            )
            data.append({
                'contact_id': contact.id,
                'contact_name': str(contact),
                'total_amount': total_amount,
                'total_accrued_interest': total_accrued_interest,
            })
        return Response(data)
