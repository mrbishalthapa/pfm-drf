import re
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from accounts.models import Contact
from .models import *
from django.db import transaction, IntegrityError
from django.db.models import Q

# 
from decimal import Decimal
from django.utils import timezone



User = get_user_model()



class LoanTransactionSerializer(serializers.ModelSerializer):
    """Serializer for creating LoanTransaction model"""

    class Meta:
        model = LoanTransaction
        fields = "__all__"
        read_only_fields = ['id']


class LoanSerializer(serializers.ModelSerializer):
    """Serializer for Loan model"""
    amount = serializers.SerializerMethodField()
    interest = serializers.SerializerMethodField()

    

    class Meta:
        model = Loan
        fields = "__all__"
        read_only_fields = ['id', 'user']

    def get_amount(self, obj):
        return obj.get_total_amount()

    def get_interest(self, obj):
        """
        Calculate outstanding interest: total accrued interest - total interest payments.
        """

        principal_balance = Decimal('0.00')
        last_date = None
        today = timezone.now()
        total_accrued_interest = Decimal('0.00')
        daily_rate = (obj.interest_rate / Decimal('100')) / Decimal('365')


        # Only consider disbursement and principal_payment transactions for interest calculation
        transactions = obj.transactions.filter(
            type__in=[
                LoanTransaction.TransactionType.DISBURSEMENT,
                LoanTransaction.TransactionType.PRINCIPAL_PAYMENT
            ]
        ).order_by('transaction_date')

        for tx in transactions:
            tx_date = min(tx.transaction_date, today)
            if last_date is not None:
                days = (tx_date - last_date).days
                if days > 0 and principal_balance > 0:
                    accrued = principal_balance * daily_rate * Decimal(days)
                    print(f"{days} * {principal_balance} * {daily_rate} = {accrued}")
                    total_accrued_interest += accrued
            # Update principal balance
            if tx.type == LoanTransaction.TransactionType.DISBURSEMENT:
                principal_balance += tx.amount
            elif tx.type == LoanTransaction.TransactionType.PRINCIPAL_PAYMENT:
                principal_balance -= tx.amount
                if principal_balance < 0:
                    principal_balance = Decimal('0.00')
            # Move last_date forward
            last_date = tx_date

        # Accrue interest from last transaction date to today if principal remains
        if last_date is not None and principal_balance > 0:
            days = (today - last_date).days + 1
            if days > 0:
                accrued = principal_balance * daily_rate * Decimal(days)
                print(f"{days} * {principal_balance} * {daily_rate} = {accrued}")
                total_accrued_interest += accrued

        accrued_interest = round(total_accrued_interest, 2)

        total_interest_paid = obj.transactions.filter(
            type=LoanTransaction.TransactionType.INTEREST_PAYMENT
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

        return accrued_interest - total_interest_paid


    def to_representation(self, instance):
        from accounts.serializers import ContactSerializer
        representation = super().to_representation(instance)
        representation['contact'] = ContactSerializer(instance.contact).data if instance.contact else None
        return representation
  


    
   