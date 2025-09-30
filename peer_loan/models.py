from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.db.models import Sum

from django.utils import timezone
from django.conf import settings
from django.db.models import TextChoices
from accounts.models import Contact
import uuid

User = get_user_model()

class Loan(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CLOSED = 'closed', 'Closed'
        DEFAULTED = 'defaulted', 'Defaulted'

    class Meta:
        unique_together = ('contact', 'interest_rate')

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=False, blank=False, related_name='loans_given')
    is_lending = models.BooleanField(default=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2) 
    status = models.CharField( max_length=20, choices=Status.choices, default=Status.ACTIVE )
    create_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)


    def get_total_amount(self):
        """
        Returns the outstanding principal amount of the loan,
        i.e., the sum of all disbursement transactions minus principal payments.
        """
        disbursed = self.transactions.filter(
            type=LoanTransaction.TransactionType.DISBURSEMENT
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        principal_paid = self.transactions.filter(
            type=LoanTransaction.TransactionType.PRINCIPAL_PAYMENT
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return disbursed - principal_paid

    




class LoanTransaction(models.Model):
    class TransactionType(models.TextChoices):
        DISBURSEMENT = 'disbursement', 'Disbursement'
        PRINCIPAL_PAYMENT = 'principal_payment', 'Principal Payment'
        INTEREST_PAYMENT = 'interest_payment', 'Interest Payment'

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField( max_length=20, choices=TransactionType.choices, default=TransactionType.DISBURSEMENT )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateTimeField() 
    remarks = models.TextField(blank=True)







# class Loan(models.Model):
#     class Status(models.TextChoices):
#         ACTIVE = 'active', 'Active'
#         INTEREST_PENDING = 'interest_pending', 'Pending'
#         CLOSED = 'closed', 'Closed'
#         DEFAULTED = 'defaulted', 'Defaulted'

#     user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='loans')
#     contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=False, blank=False, related_name='loans_given')
#     is_lending = models.BooleanField(default=True)
#     amount = models.DecimalField(max_digits=12, decimal_places=2)
#     interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # annual %
#     start_date = models.DateTimeField()
#     maturity_date = models.DateField(null=True, blank=True)
#     status = models.CharField( max_length=20, choices=Status.choices, default=Status.ACTIVE )
#     remarks = models.TextField(blank=True)
#     create_at=models.DateTimeField(auto_now_add=True)
#     updated_at=models.DateTimeField(auto_now=True)



    # def outstanding_principal(self):
    #     paid = self.transactions.filter(type='principal_payment') \
    #                             .aggregate(models.Sum('amount'))['amount__sum'] or 0
    #     return self.amount - paid


    # def calculate_outstanding_interest(self, as_of_date=None):
    #     """
    #     Total accrued interest - total interest payments
    #     """
    #     if as_of_date is None:
    #         as_of_date = timezone.now()

    #     daily_rate = (self.interest_rate / Decimal('100')) / Decimal('365')
    #     print('daily_rate',daily_rate )
    #     remaining_principal = self.amount
    #     accrued_interest = Decimal('0.00')
    #     last_date = self.start_date

    #     # ✅ Step 1: Interest accrual with principal payments
    #     principal_payments = self.transactions.filter(
    #         type='principal_payment',
    #         transaction_date__lte=as_of_date
    #     ).order_by('transaction_date')

    #     for p in principal_payments:
    #         days = (p.transaction_date - last_date).days
    #         if days > 0:
    #             print(f"interest from {last_date} to {p.transaction_date} ({days}) days : {remaining_principal * daily_rate * Decimal(days)}")
    #             accrued_interest += remaining_principal * daily_rate * Decimal(days)
    #         remaining_principal -= p.amount
    #         last_date = p.transaction_date

      

    #     # Remaining period until as_of_date
    #     days_remaining = (as_of_date - last_date).days
    #     if days_remaining > 0:
    #         print(f"interest from {last_date} to {as_of_date} ({days_remaining}) days : {remaining_principal * daily_rate * Decimal(days_remaining)}")
    #         accrued_interest += remaining_principal * daily_rate * Decimal(days_remaining)


    #     # ✅ Step 2: Subtract any interest already paid
    #     interest_paid = self.transactions.filter(
    #         type='interest_payment',
    #         transaction_date__lte=as_of_date
    #     ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    #     outstanding_interest = accrued_interest - interest_paid

    #     print('loan', self.id, 'outstanding_interest', outstanding_interest, accrued_interest, interest_paid)
    #     return outstanding_interest

    
    # # def outstanding_interest(self):
    # #     """Calculate outstanding interest amount"""
    # #     # Calculate total interest that should have been paid up to today
    # #     total_interest_due = self.calculate_total_interest_due()
        
    # #     # Calculate total interest actually paid
    # #     interest_paid = self.transactions.filter(type='interest_payment') \
    # #                                     .aggregate(models.Sum('amount'))['amount__sum'] or 0
        
    # #     return total_interest_due - interest_paid
    
    # def calculate_total_interest_due(self):
    #     """Calculate total interest due up to today based on daily calculation"""
    #     from datetime import date
        
    #     today = date.today()
    #     start_date = self.start_date
        
    #     # Calculate days elapsed since start date
    #     days_elapsed = (today - start_date).days
        
    #     # Calculate daily interest rate (annual rate / 365 days)
    #     daily_rate = self.interest_rate / 100 / 365
        
    #     # Calculate total interest due
    #     total_interest = self.principal_amount * daily_rate * days_elapsed
        
    #     return total_interest
   
    
    # @property
    # def total_outstanding(self):
    #     """Get total outstanding amount (principal + interest)"""
    #     return self.outstanding_principal() + self.outstanding_interest()



# class LoanTransaction(models.Model):


#     class TransactionType(models.TextChoices):
#         DISBURSEMENT = 'disbursement', 'Disbursement'
#         PRINCIPAL_PAYMENT = 'principal_payment', 'Principal Payment'
#         INTEREST_PAYMENT = 'interest_payment', 'Interest Payment'


#     loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='transactions')
#     type = models.CharField( max_length=20, choices=TransactionType.choices, default=TransactionType.DISBURSEMENT )
#     amount = models.DecimalField(max_digits=12, decimal_places=2)
#     transaction_date = models.DateTimeField() # incase of principal/interest payment same transaction date means it was paid in bulk
#     remarks = models.TextField(blank=True)