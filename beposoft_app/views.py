from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
import jwt
from itertools import product
from .serializers import *
from .models import User
from django.contrib.auth.hashers import check_password, make_password
from datetime import datetime, timedelta
from django.db.models import Q
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, DecodeError
from django.contrib.auth import authenticate
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError


class UserRegistrationAPIView(APIView):
    def post(self, request):
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": "success",
                    "message": "Registration successfully completed",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "status": "error",
                    "message": "Registration failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




class UserLoginAPIView(APIView):
    def post(self, request):
        try:
            serializer = UserLoginSerializer(data=request.data)
            if serializer.is_valid():
                email = serializer.validated_data.get('email')
                password = serializer.validated_data.get('password')

                customer = User.objects.filter(email=email, approval_status="approved").first()

                if customer and customer.check_password(password):
                    # Generate JWT token
                    expiration_time = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
                    user_token = {
                        'id': customer.pk,  # Use ID or another unique identifier
                        'email': customer.email,
                        'exp': expiration_time,
                        'iat': datetime.utcnow()
                    }
                    token = jwt.encode(user_token, settings.SECRET_KEY, algorithm='HS256')

                    # Set JWT token in cookies
                    response = Response({
                        "status": "success",
                        "message": "Login successful",
                        "token": token,
                        "active": customer.department_id.name
                    }, status=status.HTTP_200_OK)
                    response.set_cookie(
                        key='token',
                        value=token,
                        httponly=True,
                        samesite='Lax',
                        secure=settings.SECURE_COOKIE  # Ensure this matches your settings
                    )
                    return response
                else:
                    return Response({
                        "status": "error",
                        "message": "Invalid email or password"
                    }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({
                    "status": "error",
                    "message": "Invalid data",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": "error",
                "message": "An error occurred",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class UserProfileData(APIView):
    def get(self, request):
        try:
            # Retrieve the token from cookies
            token = request.headers.get('Authorization')
            if token is None:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                # Decode the JWT token
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')  # Correct field name should match the token payload

                # Fetch user from the database
                user = User.objects.get(pk=user_id)  # Use pk for primary key lookup
                serializer = UserSerializer(user)
                return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class CreateUserView(APIView):
    def post(self,request):
        try:
            token = request.headers.get('token')
            if token is None:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                user = User.objects.filter(pk=user_id).first()
                if user is None:
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                serializer = UserSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "message": "User Created  successfully"}, status=status.HTTP_200_OK)
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class Users(APIView):
    def get(self, request):
        try:
            users = User.objects.all()
            serializer = UserSerializer(users, many=True)
            return Response({
                "data": serializer.data,
                "message": "Users fetching is successfully completed"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "message": "An error occurred while fetching users",
                "error": str(e)  
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class UserDeleteView(APIView):
    def get(self, request, pk):
        try:
            token = request.headers.get('token')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')
                
                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                user_to_delete = User.objects.filter(pk=pk).first()
                if not user_to_delete:
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                user_to_delete.delete()
                return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class UserDataUpdate(APIView):
    def get(self,request,pk):
        try :
            token = request.headers.get('token')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')
                
                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                user = User.objects.filter(pk=pk).first()
                if not user:
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                serilizer = UserSerializer(user, many=False)
                return Response({"message": "User fetched successfully","data":serilizer.data}, status=status.HTTP_200_OK)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def put(self,request,pk):
        try :
            token = request.headers.get('token')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')
                
                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                user = User.objects.filter(pk=pk).first()
                if not user:
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                serilizer = UserSerializer(user, data=request.data)
                if serilizer.is_valid():
                    serilizer.save()
                    return Response({"message": "User updated successfully","data":serilizer.data}, status=status.HTTP_200_OK)
                return Response({"message": "error","error":serilizer.errors}, status=status.HTTP_200_OK)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





            


class UserCustomerAddingView(APIView):
    def post(self, request):
        token = request.headers.get("Authorization")
        
        if token is None:
            return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            # Decode the JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('id')
            print(user_id)
            
            # Check if the user exists
            user = User.objects.filter(id=user_id).first()
            if user is None:
                return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = CustomerModelSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"data": serializer.data, "message": "Customer added successfully"}, status=status.HTTP_201_CREATED)
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except jwt.ExpiredSignatureError:
            return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            print(e)
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
class CustomerView(APIView):
    def get(self, request):
        try:
            token = request.headers.get("Authorization")
            if token is None:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                user = User.objects.filter(pk=user_id).first()
                if user is None:
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                customers = Customers.objects.all()
                serializer = CustomerModelSerializer(customers, many=True)
                return Response({"data": serializer.data, "message": "Customers retrieved successfully"}, status=status.HTTP_200_OK)
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CustomerUpdateView(APIView):
    def get(self,request,pk):
        try:
            token = request.headers.get("Authorization")
            if token is None:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                user = User.objects.filter(pk=user_id).first()
                if user is None:
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                customers = Customers.objects.filter(pk=pk).first()
                serializer = CustomerModelSerializer(customers, many=False)
                return Response({"data": serializer.data, "message": "Customers retrieved successfully"}, status=status.HTTP_200_OK)
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def put(self, request, pk):
        try:
            token = request.headers.get("Authorization")
            if token is None:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                user = User.objects.filter(pk=user_id).first()
                if user is None:
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                customer = Customers.objects.filter(pk=pk).first()
                if customer is None:
                    return Response({"message": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
                
                serializer = CustomerModelSerializer(customer, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "message": "Customer updated successfully"}, status=status.HTTP_200_OK)
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class CustomerDeleteView(APIView):
    def get(self,request,pk):
        try:
            token = request.headers.get("Authorization")
            if token is None:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                user = User.objects.filter(pk=user_id).first()
                if user is None:
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                customers = Customers.objects.filter(pk=pk).first()
                serializer = CustomerModelSerializer(customers, many=False)
                return Response({"data": serializer.data, "message": "Customers retrieved successfully"}, status=status.HTTP_200_OK)
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self,request,pk):
        try:
            token = request.headers.get("Authorization")
            if token is None:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                user = User.objects.filter(pk=user_id).first()
                if user is None:
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                customer = Customers.objects.filter(pk=pk).first()
                if customer is None :
                    return Response({"message":"Customer not found"},status=status.HTTP_404_NOT_FOUND)
                customer.delete()
                return Response({"message": "Customer deleted successfully"}, status=status.HTTP_200_OK)
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


            

class FamilyCreatView(APIView):
    def post(self, request):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = FamilySerilizers(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"message": "Family added successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
                return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class FamilyAllView(APIView):
    def get(self, request):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                family = Family.objects.all()
                serializer = FamilySerilizers(family, many=True)
                return Response({"message": "Family list successfully retrieved", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




class FamilyDataDelete(APIView):

    def get(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                family = Family.objects.filter(pk=pk).first()
                if not family:
                    return Response({"message": "Family not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = FamilySerilizers(family)
                return Response({"message": "Family fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                family = Family.objects.filter(pk=pk).first()
                if not family:
                    return Response({"message": "Family not found"}, status=status.HTTP_404_NOT_FOUND)

                family.delete()
                return Response({"message": "Family deleted successfully"}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

class FamilyUpdateView(APIView):

    def get(self, request, pk):

        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                family = Family.objects.filter(pk=pk).first()
                if not family:
                    return Response({"message": "Family not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = FamilySerilizers(family)
                return Response({"message": "Family fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def put(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                family = Family.objects.filter(pk=pk).first()
                if not family:
                    return Response({"message": "Family not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = FamilySerilizers(family, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"message": "Family updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        





class ProductCreateView(APIView):
    def post(self, request):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                user = User.objects.filter(pk=user_id).first()
                if not user:
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = ProductSerilizers(data=request.data)
                if serializer.is_valid():
                    serializer.save(created_user=user)
                    return Response({"message": "Product added successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
                return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class ProductListView(APIView):
    def get(self, request):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                product = Products.objects.all()
                serializer = ProductSerilizers(product, many=True)
                return Response({"message": "Product list successfully retrieved", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class ProductDeleteView(APIView):
    def get(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                product = Products.objects.filter(pk=pk).first()
                if not product:
                    return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = ProductSerilizers(product)
                return Response({"message": "Product fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                product = Products.objects.filter(pk=pk).first()
                if not product:
                    return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

                product.delete()
                return Response({"message": "Product deleted successfully"}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class ProductUpdateView(APIView):
    def get(self, request, pk):

        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                product = Products.objects.filter(pk=pk).first()
                if not product:
                    return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = ProductSerilizers(product)
                return Response({"message": "Product fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def put(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                product = Products.objects.filter(pk=pk).first()
                if not product:
                    return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = ProductSerilizers(product, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"message": "Product updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                
                return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class DepartmentCreateView(APIView):
    def post(self,request):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                user = User.objects.filter(pk=user_id).first()
                if not user:
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = DepartmentSerilizers(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"message": "Departmen added successftully", "data": serializer.data}, status=status.HTTP_201_CREATED)
                print(serializer.errors)
                return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class DepartmentListView(APIView):
    def get(self, request):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                department = Departments.objects.all()
                serializer = DepartmentSerilizers(department, many=True)
                return Response({"message": "Departments list successfully retrieved", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class DepartmentDeleteView(APIView):
    def get(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                department = Departments.objects.filter(pk=pk).first()
                if not department:
                    return Response({"message": "Department not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = DepartmentSerilizers(department)
                return Response({"message": "Departments fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                department = Departments.objects.filter(pk=pk).first()
                if not department:
                    return Response({"message": "Departments not found"}, status=status.HTTP_404_NOT_FOUND)

                department.delete()
                return Response({"message": "Departments deleted successfully"}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class DepartmentsUpdateView(APIView):
    def get(self, request, pk):

        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                department = Departments.objects.filter(pk=pk).first()
                if not department:
                    return Response({"message": "Department not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = DepartmentSerilizers(department)
                return Response({"message": "Department fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def put(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                department = Departments.objects.filter(pk=pk).first()
                if not department:
                    return Response({"message": "Department not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = DepartmentSerilizers(department, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"message": "Department updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                
                return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class StateCreateView(APIView):
    def post(self, request):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = StateSerializers(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"message": "State added successftully", "data": serializer.data}, status=status.HTTP_201_CREATED)
                return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class StateListView(APIView):
    def get(self, request):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                state = State.objects.all()
                serializer = StateSerializers(state, many=True)
                return Response({"message": "State list successfully retrieved", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class StateDeleteView(APIView):
    def get(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                state = State.objects.filter(pk=pk).first()
                if not state:
                    return Response({"message": "State not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = StateSerializers(state)
                return Response({"message": "State fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                state = State.objects.filter(pk=pk).first()
                if not state:
                    return Response({"message": "State not found"}, status=status.HTTP_404_NOT_FOUND)

                state.delete()
                return Response({"message": "State deleted successfully"}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class StateUpdateView(APIView):
    def get(self, request, pk):

        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                state = State.objects.filter(pk=pk).first()
                if not state:
                    return Response({"message": "State not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = StateSerializers(state)
                return Response({"message": "State fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def put(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                state = State.objects.filter(pk=pk).first()
                if not state:
                    return Response({"message": "State not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = StateSerializers(state, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"message": "State updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                
                return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class SupervisorCreateView(APIView):
    def post(self, request):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = SupervisorSerializers(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"message": "Supervisor added successftully", "data": serializer.data}, status=status.HTTP_201_CREATED)
                return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SuperviserListView(APIView):
    def get(self, request):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                supervisor = Supervisor.objects.all()
                serializer = SupervisorViewSerializers(supervisor, many=True)
                return Response({"message": "Supervisor list successfully retrieved", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SupervisorDeleteView(APIView):
    def get(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                supervisor = Supervisor.objects.filter(pk=pk).first()
                if not supervisor:
                    return Response({"message": "Supervisor not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = SupervisorSerializers(supervisor)
                return Response({"message": "Supervisor fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                supervisor = Supervisor.objects.filter(pk=pk).first()
                if not supervisor:
                    return Response({"message": "Supervisor not found"}, status=status.HTTP_404_NOT_FOUND)

                supervisor.delete()
                return Response({"message": "Supervisor deleted successfully"}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class SupervisorUpdateView(APIView):
    def get(self, request, pk):
        
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                supervisor = Supervisor.objects.filter(pk=pk).first()
                if not supervisor:
                    return Response({"message": "Supervisor not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = SupervisorSerializers(supervisor)
                return Response({"message": "Supervisor fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def put(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                supervisor = Supervisor.objects.filter(pk=pk).first()
                if not supervisor:
                    return Response({"message": "Supervisor not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = SupervisorSerializers(supervisor, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"message": "Supervisor updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                
                return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ShippingCreateView(APIView):
    def post(self, request,pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                customer = Customers.objects.filter(pk=pk).first()
                if not customer:
                    return Response({"message": "customer not found"}, status=status.HTTP_404_NOT_FOUND)
                

                serializer = ShippingSerializers(data=request.data,)
                if serializer.is_valid(customer=customer.pk):
                    serializer.save()
                    return Response({"message": "Shipping Address Add successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                
                return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




class CustomerShippingAddress(APIView):
    def get(self, request,pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                customer = Customers.objects.filter(pk=pk).first()
                if not customer:
                    return Response({"message": "customer not found"}, status=status.HTTP_404_NOT_FOUND)
                
                shipping = Shipping.objects.filter(customer=customer)
                serializer = ShippingSerializers(shipping, many=True)
                return Response({"message": "Shipping Address List successfully", "data": serializer.data}, status=status.HTTP_200_OK)
            
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CustomerShippingAddressDelete(APIView):
    def delete(self, request,pk):
        try:
            token = request.hedaers.get('Authorization')
            if token is None :
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                address = Shipping.objects.filter(pk=pk).first()
                if not address:
                    return Response({"message": "address not found"}, status=status.HTTP_404_NOT_FOUND)
                
                address.delete()
                return Response({"message": "Customer address deleted successfully"}, status=status.HTTP_200_OK)
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            
            
class CustomerShippingAddressUpdate(APIView):
    def get(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                address = Shipping.objects.filter(pk=pk).first()
                if not address:
                    return Response({"message": "address not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = ShippingSerializers(address)
                return Response({"message": "Address fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def put(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                address = Shipping.objects.filter(pk=pk).first()
                if not address:
                    return Response({"message": "address not found"}, status=status.HTTP_404_NOT_FOUND)

                serializer = ShippingSerializers(address, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"message": "address updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                
                return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class VariantProductCreate(APIView):
    def post(self, request):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                # Get request data
                product_id = request.data.get("product")
                attributes = request.data.get("attributes")

                # Fetch product
                try:
                    product_instance = Products.objects.get(pk=product_id)
                except Products.DoesNotExist:
                    return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

                # Process attributes
                attribute_values = {}
                for attr in attributes:
                    attr_name = attr.get("attribute")
                    attr_values = attr.get("value").split(", ")
                    attribute_values[attr_name] = attr_values

                # Generate combinations and save VariantProducts
                combinations = product(*attribute_values.values())
                for combination in combinations:
                    name = " - ".join([f"{value}" for attr_name, value in zip(attribute_values.keys(), combination)])
                    VariantProducts.objects.create(
                        created_user=User.objects.get(pk=user_id),
                        product=product_instance,  
                        name=name,
                    )

                return Response({"message": "Variant products added successfully"}, status=status.HTTP_201_CREATED)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class VariantProductsByProductView(APIView):
    def get(self, request, product_id):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                variant_products = VariantProducts.objects.filter(product=product_id)
                if not variant_products.exists():
                    return Response({"message": "No variant products found for this product"}, status=status.HTTP_404_NOT_FOUND)
                
                serializer = VariantProductSerializer(variant_products, many=True)
                return Response({"variant_products": serializer.data}, status=status.HTTP_200_OK)
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class VariantProductDetailView(APIView):
    def get(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                variant_product = VariantProducts.objects.get(pk=pk)
                serializer = VariantProductSerializer(variant_product)
                return Response({"variant_product": serializer.data}, status=status.HTTP_200_OK)
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except VariantProducts.DoesNotExist:
            return Response({"message": "Variant product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                variant_product = VariantProducts.objects.filter(pk=pk).first()
                serializer = VariantProductSerializer(variant_product, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"message": "Variant product updated successfully", "variant_product": serializer.data}, status=status.HTTP_200_OK)
                return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        except VariantProducts.DoesNotExist:
            return Response({"message": "Variant product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                variant_product = VariantProducts.objects.filter(pk=pk).first()
                variant_product.delete()
                return Response({"message": "Variant product deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except VariantProducts.DoesNotExist:
            return Response({"message": "Variant product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class SingleProductCreate(APIView):
    def post(self, request):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                user = User.objects.filter(pk=user_id).first()
                if not user:
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

                product_instance = request.data.get('product')
                product = Products.objects.filter(pk=product_instance).first()
                if not product:
                    return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

                if product.type == "single":
                    serializer = SingleProductSerializer(data=request.data, context={'created_user': user})
                    if serializer.is_valid():
                        serializer.save()
                        return Response({"data": serializer.data, "message": "Product stock added successfully"}, status=status.HTTP_201_CREATED)
                    return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"message": "Product type is not single"}, status=status.HTTP_400_BAD_REQUEST)

            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        except SingleProducts.DoesNotExist:
            return Response({"message": "Single product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class SingleProductDetailView(APIView):
    def get(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                single_product = SingleProducts.objects.get(pk=pk)
                serializer = SingleProductSerializer(single_product)
                return Response({"single_product": serializer.data}, status=status.HTTP_200_OK)
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except VariantProducts.DoesNotExist:
            return Response({"message": "Single product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                single_product = SingleProducts.objects.filter(pk=pk).first()
                serializer = SingleProductSerializer(single_product, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"message": "Single product updated successfully", "single_product": serializer.data}, status=status.HTTP_200_OK)
                return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        except VariantProducts.DoesNotExist:
            return Response({"message": "Single product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                single_product = SingleProducts.objects.filter(pk=pk).first()
                single_product.delete()
                return Response({"message": "Single product deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except VariantProducts.DoesNotExist:
            return Response({"message": "Variant product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class SingleProductsByProductView(APIView):
    def get(self, request, product_id):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')

                if not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                
                single_product = SingleProducts.objects.filter(product=product_id)
                if not single_product.exists():
                    return Response({"message": "No variant products found for this product"}, status=status.HTTP_404_NOT_FOUND)
                
                serializer = SingleProductSerializer(single_product, many=True)
                return Response({"single_product": serializer.data}, status=status.HTTP_200_OK)
            
            except jwt.ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        


class CreateOrder(APIView):
    def post(self, request):
        token = request.headers.get('Authorization')
        if not token:
            return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            # Decode JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('id')

            if not User.objects.filter(pk=user_id).exists():
                return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Deserialize request data
            serializer = OrderSerializer(data=request.data)
            
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success", "message": "Order created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
            
            # Handle validation errors
            return Response({"status": "error", "message": "Validation failed", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except jwt.ExpiredSignatureError:
            return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except jwt.InvalidTokenError:
            return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            return Response({"status": "error", "message": "An unexpected error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class OrderListView(APIView):
    def get(self, request):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')
                if not user_id or not User.objects.filter(pk=user_id).exists():
                    return Response({"message": "User not found or invalid token"}, status=status.HTTP_404_NOT_FOUND)
            except ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except (DecodeError, InvalidTokenError):
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

            orders = OrderItem.objects.all()
            if not orders.exists():
                return Response({"status": "error", "message": "No orders found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = OrderItemModelSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Orders not found"}, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError:
            return Response({"status": "error", "message": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class CustomerOrderList(APIView):
    def get(self, request):
        try:
            # Retrieve the token from the headers
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                # Decode and validate the token
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')
                
                # Fetch the user
                user = User.objects.filter(pk=user_id).first()
                if not user:
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            except ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except (DecodeError, InvalidTokenError):
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

            # Fetch orders managed by the user
            orders = Order.objects.filter(manage_staff=user)
            if not orders.exists():
                return Response({"status": "error", "message": "No orders found"}, status=status.HTTP_404_NOT_FOUND)

            # Serialize and return the orders
            serializer = OrderModelSerilizer(orders, many=True)
            return Response({"data":serializer.data}, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Orders not found"}, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError:
            return Response({"status": "error", "message": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class CustomerOrderItems(APIView):
    def get(self, request, order_id):
        try:
            token = request.headers.get('Authorization')
            if not token:
                return Response({"status": "Unauthorized", "message": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('id')
                
                user = User.objects.filter(pk=user_id).first()
                if not user:
                    return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            except ExpiredSignatureError:
                return Response({"status": "error", "message": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except (DecodeError, InvalidTokenError):
                return Response({"status": "error", "message": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            
            order = Order.objects.filter(pk=order_id).first()
            orderItems = OrderItem.objects.filter(order=order_id)
            if not orderItems.exists():
                return Response({"status": "error", "message": "No orders Items found"}, status=status.HTTP_404_NOT_FOUND)
            
            orderSerilizer = OrderModelSerilizer(order, many=False)
            serializer = OrderItemModelSerializer(orderItems, many=True)
            return Response({"order":orderSerilizer.data,"items":serializer.data}, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Orders not found"}, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError:
            return Response({"status": "error", "message": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



# class OrderStatusUpdate()