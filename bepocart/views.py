from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from beposoft_app.models import Products
from .serializers import ProductSerilizers
from rest_framework.response import Response
from .models import*
from .serializers import LoanSerializer
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, DecodeError
from django.conf import settings
from beposoft_app.models import User


class ProductListView(APIView):
    def get(self,request):
        products = Products.objects.all()
        serializer = ProductSerilizers(products, many=True)
        return Response(serializer.data)
        
class BaseTokenView(APIView):
      def get_user_from_token(self, request):
        token = request.headers.get('Authorization')
        
        if not token:
            return None, Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not token.startswith("Bearer "):
            return None, Response({"status": "error", "message": "Token must start with 'Bearer '"}, status=status.HTTP_401_UNAUTHORIZED)
        
        token = token.split(" ")[1]

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('id')
            user = User.objects.filter(pk=user_id, approval_status="approved").first()

            if not user:
                return None, Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            return user, None
        
        except jwt.ExpiredSignatureError:
            return None, Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except jwt.InvalidTokenError:
            return None, Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            return None, Response({"status": "error", "message": "An error occurred while decoding the token", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EmiView(BaseTokenView):
    def post(self, request):
        """Create a loan entry and calculate EMI."""
        try:
            # Authenticate user from token
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            serializer = LoanSerializer(data=request.data)
            if serializer.is_valid():
                loan = serializer.save(user=authUser)  # Associate loan with authenticated user
                
                # EMI Calculation
                P = loan.principal - (loan.down_payment or 0)
                R = (loan.annual_interest_rate / 12) / 100
                N = loan.tenure_months

                if R == 0:  # Zero interest case
                    emi = P / N
                else:
                    emi = (P * R * (1 + R) ** N) / ((1 + R) ** N - 1)

                return Response({
                    "message": "EMI calculated successfully",
                    "data": serializer.data,
                    "emi": round(emi, 2)
                }, status=status.HTTP_201_CREATED)

            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """Fetch all loans associated with the authenticated user."""
        try:
            # Authenticate user from token
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            # Fetch loans of the authenticated user
            loans = Loan.objects.filter(user=authUser)
            serializer = LoanSerializer(loans, many=True)

            return Response({
                "message": "User loans retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class LoanEMIView(APIView):
    """Retrieve EMI details for a specific loan by ID"""

    def get(self, request, loan_id):
        try:
            # Fetch the loan object by ID or return 404 if not found
            loan = get_object_or_404(Loan, id=loan_id)

            # Serialize loan data (emi is now included)
            serializer = LoanSerializer(loan)

            # Return response with EMI inside loan details
            return Response({
                "message": "Loan details retrieved successfully",
                "loan_details": serializer.data  # EMI is already inside this
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)                        
        


class EmiExpenseView(BaseTokenView):
    def get(self, request, emi_id=None):
        """Fetch all loans for the user or specific EMI expenses if emi_id is provided."""
        try:
            # Authenticate user from token
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            if emi_id:
                return self.get_loan_expenses(authUser, emi_id)
            else:
                return self.get_user_loans(authUser)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "An error occurred",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_loan_expenses(self, user, emi_id):
        """Fetch detailed EMI expenses for a specific loan."""
        loan = get_object_or_404(Loan, id=emi_id, user=user)

        # Fetching EMI-related expenses
        expenses = ExpenseModel.objects.filter(loan=loan, purpose_of_payment="emi").values("expense_date", "amount")

        # Calculating total amount paid (including down payment)
        total_emi_paid = sum(exp["amount"] for exp in expenses)
        total_amount_paid = loan.down_payment + total_emi_paid  # Adding down payment to EMI payments

        # Structuring EMI data
        emi_data = {
            "emi_name": loan.emi_name,
            "principal": loan.principal,
            "tenure_months": loan.tenure_months,
            "annual_interest_rate": loan.annual_interest_rate,
            "down_payment": loan.down_payment,
            "emi_amount":loan.emi_amount,
            "total_interest":loan.total_interest,
            "total_payment":loan.total_payment,
            "total_emi_paid": total_emi_paid,  # Only EMI payments
            "total_amount_paid": total_amount_paid,  # EMI + Down Payment
            "emidata": [{"date": exp["expense_date"], "amount": exp["amount"]} for exp in expenses]
        }

        return Response(emi_data, status=status.HTTP_200_OK)

    def get_user_loans(self, user):
        """Fetch all EMI loans along with their expenses."""
        loans = Loan.objects.filter(user=user)

        response_data = []
        for loan in loans:
            # Fetching all EMI expenses related to this loan
            expenses = ExpenseModel.objects.filter(loan=loan, purpose_of_payment="emi").values("expense_date", "amount")
            
            total_emi_paid = sum(exp["amount"] for exp in expenses)
            total_amount_paid = loan.down_payment + total_emi_paid  # Adding down payment to EMI payments

            # Structuring the response
            loan_data = {
                "id": loan.id,
                "emi_name": loan.emi_name,
                "principal": loan.principal,
                "tenure_months": loan.tenure_months,
                "annual_interest_rate": loan.annual_interest_rate,
                "down_payment": loan.down_payment,
                "emi_amount":loan.emi_amount,
                 "total_interest":loan.total_interest,
                 "total_payment":loan.total_payment,
                "total_emi_paid": total_emi_paid,  # Only EMI payments
                "total_amount_paid": total_amount_paid,  # EMI + Down Payment
                "emidata": [{"date": exp["expense_date"], "amount": exp["amount"]} for exp in expenses]
            }
            response_data.append(loan_data)

        return Response(response_data, status=status.HTTP_200_OK)