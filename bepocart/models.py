from django.db import models
from django.contrib.auth.models import User
from beposoft_app.models import User

class Loan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True, blank=True)
    principal = models.DecimalField(max_digits=15, decimal_places=2, help_text="Total loan amount")
    annual_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual interest rate in %")
    tenure_months = models.IntegerField(help_text="Loan duration in months")
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Optional processing fee")
    down_payment = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Initial payment to reduce loan amount")
    prepayment_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Extra payment towards principal")
    
    def calculate_emi(self):
        """Calculate EMI using the standard formula."""
        P = self.principal - (self.down_payment or 0)
        R = (self.annual_interest_rate / 12) / 100
        N = self.tenure_months

        if R == 0:  # If zero interest
            return P / N

        emi = (P * R * (1 + R) ** N) / ((1 + R) ** N - 1)
        return round(emi, 2)

    def __str__(self):
        return f"Loan: {self.principal} at {self.annual_interest_rate}% for {self.tenure_months} months"
