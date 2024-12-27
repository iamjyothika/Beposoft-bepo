from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
import jwt
import logging
import itertools
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
from decimal import Decimal
from django.db.models import Sum
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.db.models import Count, Q
from collections import defaultdict


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
                        'name':customer.name,
                        'exp': expiration_time,
                        'iat': datetime.utcnow() 
                    }
                    token = jwt.encode(user_token, settings.SECRET_KEY, algorithm='HS256')

                    # Set JWT token in cookies
                    response = Response({ "status": "success",
                        "message": "Login successful",
                        "token": token,
                        'name':customer.name,
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
        
        

class UserProfileData(BaseTokenView):
    def get(self, request):
        try:
            user, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            serializer = UserSerializer(user)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"status": "error", "message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.exception("An error occurred in UserProfileData: %s", str(e))
            return Response({"status": "error", "message": "An internal error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class CreateUserView(BaseTokenView):
    def post(self, request):
        try:
            # Validate user from token
            user, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response


            # Validate and process allocated_states
            allocated_states = request.data.get('allocated_states')
            
            # Save user data
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                user_instance = serializer.save()

                if allocated_states:
                    valid_states = State.objects.filter(pk__in=allocated_states)
                    user_instance.allocated_states.set(valid_states)
                    user_instance.save()

                return Response(
                    {
                        "data": serializer.data,
                        "message": "User created successfully"
                    },
                    status=status.HTTP_201_CREATED
                )
                
            return Response({"status": "error","message": "Validation failed","errors": serializer.errors},status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {
                    "status": "error",
                    "message": "An error occurred",
                    "errors": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class Users(BaseTokenView):
    def get(self, request):
        try:
            user, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

                        
            users = User.objects.all()
            serializer = StaffSerializer(users, many=True)
            return Response({
                "data": serializer.data,
                "message": "Users fetching is successfully completed"
            }, status=status.HTTP_200_OK)
            
        except user.DoesNotExist:
            return Response({"status": "error", "message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "message": "An error occurred while fetching users",
                "error": str(e)  
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        


class UserDataUpdate(BaseTokenView):
    def get_user(self, pk):
        return get_object_or_404(User, pk=pk)

    def get(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            user = self.get_user(pk)
            
            serializer = UserSerializer(user)
            return Response({"message": "User fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            # Authenticate the user using a token
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            # Retrieve the user object to be updated
            user = self.get_user(pk)

            # If the password is provided in the request, hash it
            if 'password' in request.data:
                request.data['password'] = make_password(request.data['password'])

            # Use partial=True to allow partial updates
            serializer = UserUpdateSerilizers(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "User updated successfully", "data": serializer.data},
                    status=status.HTTP_200_OK
                )

            return Response(
                {"status": "error", "message": "Validation error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"status": "error", "message": "An error occurred", "errors": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class UserCustomerAddingView(BaseTokenView):
    def post(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            
            data = request.data
            if isinstance(data, dict):
                data = [data]
            
            if not isinstance(data, list):
                return Response(
                    {"status": "error", "message": "Invalid data format. Must be a dictionary or list of dictionaries."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = CustomerModelSerializer(data=data, many=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"data": serializer.data, "message": "Customer added successfully"}, status=status.HTTP_201_CREATED)
           
            return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"status": "error", "message": "An internal server error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



            
class CustomerView(BaseTokenView):
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
                
            customers = Customers.objects.all()
            serializer = CustomerModelSerializerView(customers, many=True)
            return Response({"data": serializer.data, "message": "Customers retrieved successfully"}, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({"status": "error", "message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CustomerUpdateView(BaseTokenView):
    
    def get_customer(self, pk):
        return get_object_or_404(Customers, pk=pk)

    def get(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
                
            customer = self.get_customer(pk)
            serializer = CustomerSerilizers(customer)
            return Response({"data": serializer.data, "message": "Customer retrieved successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            customer = self.get_customer(pk)
            
            
            
            serializer = CustomerSerilizers(customer, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"data": serializer.data, "message": "Customer updated successfully"}, status=status.HTTP_200_OK)
            return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


            

class FamilyCreatView(BaseTokenView):
    def post(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            serializer = FamilySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Family added successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class FamilyAllView(BaseTokenView):
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            family = Family.objects.all()
            serializer = FamilySerializer(family, many=True)
            return Response({"message": "Family list successfully retrieved", "data": serializer.data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class FamilyUpdateView(BaseTokenView):
    
    def get_family(self, pk):
        return get_object_or_404(Family, pk=pk)
    
    def get(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            family = self.get_family(pk)
            serializer = FamilySerializer(family)
            return Response({"message": "Family fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    def delete(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
                
            family = self.get_family(pk)
            family.delete()
            return Response({"message": "Family deleted successfully"}, status=status.HTTP_200_OK)
                        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def put(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            family = self.get_family(pk)
            serializer = FamilySerializer(family, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Family updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class ProductCreateView(BaseTokenView):
    @transaction.atomic
    def post(self, request):
        try:
            # Authenticate user
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            # Extract and validate family IDs
            family_ids = request.data.get('family')
            if not family_ids:
                return Response({"message": "No family IDs provided"}, status=status.HTTP_400_BAD_REQUEST)

            families = Family.objects.filter(pk__in=family_ids)
            if families.count() != len(family_ids):
                invalid_ids = set(family_ids) - set(families.values_list('id', flat=True))
                return Response({"message": "Invalid family IDs", "invalid_ids": list(invalid_ids)}, status=status.HTTP_400_BAD_REQUEST)

            # Add created_user to request data
            request.data['created_user'] = authUser.pk

            # Validate and save product
            serializer = ProductsSerializer(data=request.data)
            if serializer.is_valid():
                product = serializer.save()
                product.family.set(families)  # Associate families with product
                return Response({"message": "Product added successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
            
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except KeyError as e:
            return Response({"message": f"Missing required field: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductListView(BaseTokenView):
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            # Fetch all products
            products = Products.objects.all()

            # Initialize a set to track unique groupIDs
            seen_group_ids = set()
            unique_products = []

            # Iterate through products and filter out duplicates by groupID
            for product in products:
                if product.groupID not in seen_group_ids:
                    seen_group_ids.add(product.groupID)
                    unique_products.append(product)

            # Serialize the unique products list
            serializer = ProductSingleviewSerializres(unique_products, many=True)

            return Response({
                "message": "Product list successfully retrieved",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except authUser.DoesNotExist:
            return Response({
                "status": "error",
                "message": "User does not exist"
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "An error occurred",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
class ListAllProducts(BaseTokenView):  
    def get(self, request):
        auth_user, error_response = self.get_user_from_token(request)
        if error_response:
            return error_response

        try:
            products = Products.objects.all()
            serializer = ProductsListViewSerializers(products, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching products: {str(e)}")
            return Response({
                "error": "An error occurred while retrieving products. Please try again later."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            



class ProductUpdateView(BaseTokenView):
    
    def get_product(self,pk):
        return get_object_or_404(Products, pk=pk)
    
    def get(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            product = self.get_product(pk)

            serializer = ProductSerializerView(product)
            return Response({"message": "Product fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    def delete(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
                
            product = self.get_product(pk)
            product.delete()
            return Response({"message": "Product deleted successfully"}, status=status.HTTP_200_OK)
                            
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        

    def put(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            product = self.get_product(pk)

            serializer = ProductsSerializer(product, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Product updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class SingleProductImageCreateView(BaseTokenView):
    def post(self, request, pk):
        try:
            # Get authenticated user
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            # Get the product
            product = get_object_or_404(Products, pk=pk)

            images = request.FILES.getlist('images')
            if not images:
                return Response({"message": "No images were uploaded"}, status=status.HTTP_400_BAD_REQUEST)

            saved_images = []

            if product.type == "single":
                for image in images:
                    single_product = SingleProducts.objects.create(product=product, created_user=authUser, image=image)
                    saved_images.append(single_product)
            elif product.type == "variant":
                products_to_update = Products.objects.filter(groupID=product.groupID, color=product.color)
                for prod in products_to_update:
                    for image in images:
                        variant_product = SingleProducts.objects.create(product=prod, created_user=authUser, image=image)
                        saved_images.append(variant_product)

            return Response({
                "message": f"{len(saved_images)} images added successfully",
                "saved_images": [img.id for img in saved_images]  ##d d dd
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "An error occurred",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            

class SingleProductImageView(BaseTokenView):
    def delete(self,request,pk):
        try :
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            image = get_object_or_404(SingleProducts,pk=pk)
            image.delete()
            return Response({"message":"Image deleted successfuly completed"},status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            


class DepartmentCreateView(BaseTokenView):
    def post(self,request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            serializer = DepartmentSerilizers(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Departmen added successftully", "data": serializer.data}, status=status.HTTP_201_CREATED)
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class DepartmentListView(BaseTokenView):
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
                
            department = Departments.objects.all()
            serializer = DepartmentSerilizers(department, many=True)
            return Response({"message": "Departments list successfully retrieved", "data": serializer.data}, status=status.HTTP_200_OK)
                            
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    

class DepartmentsUpdateView(BaseTokenView):
    
    def get_department(self, pk):
        return get_object_or_404(Departments, pk=pk)
    
    
    def get(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            department = self.get_department(pk)
            serializer = DepartmentSerilizers(department)
            
            return Response({"message": "Department fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def put(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            department = self.get_department(pk)
            
            serializer = DepartmentSerilizers(department, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Department updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
            
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    def delete(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
                
            department = self.get_department(pk)
            department.delete()
            return Response({"message": "Departments deleted successfully"}, status=status.HTTP_200_OK)
                                
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class StateCreateView(BaseTokenView):
    def post(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            data = request.data
            if isinstance(data, dict):
                data = [data]
            
            if not isinstance(data, list):
                return Response(
                    {"status": "error", "message": "Invalid data format. Must be a dictionary or list of dictionaries."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = StateSerializers(data=data , many=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "State added successftully", "data": serializer.data}, status=status.HTTP_201_CREATED)
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class StateListView(BaseTokenView):
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            state = State.objects.all()
            serializer = StateSerializers(state, many=True)
            return Response({"message": "State list successfully retrieved", "data": serializer.data}, status=status.HTTP_200_OK)
                            
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        

class StateUpdateView(BaseTokenView):
    def get_states(self,pk):
        return get_object_or_404(State, pk=pk)
    
    def get(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            state = self.get_states(pk)
            serializer = StateSerializers(state)
            return Response({"message": "State fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    def delete(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            state = self.get_states(pk)
            state.delete()
            return Response({"message": "State deleted successfully"}, status=status.HTTP_200_OK)
                            
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def put(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            state = self.get_states(pk)
            serializer = StateSerializers(state, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "State updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class SupervisorCreateView(BaseTokenView):
    def post(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            serializer = SupervisorSerializers(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Supervisor added successftully", "data": serializer.data}, status=status.HTTP_201_CREATED)
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SuperviserListView(BaseTokenView):
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
                
            supervisor = Supervisor.objects.all()
            serializer = SupervisorSerializerView(supervisor, many=True)
            return Response({"message": "Supervisor list successfully retrieved", "data": serializer.data}, status=status.HTTP_200_OK)
                        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        

class SupervisorUpdateView(BaseTokenView):
    def get_supervisor(self,pk):
        return get_object_or_404(Supervisor,pk=pk)
    
    def get(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            supervisor = self.get_supervisor(pk)
            serializer = SupervisorSerializers(supervisor)
            return Response({"message": "Supervisor fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def put(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            supervisor = self.get_supervisor(pk)

            serializer = SupervisorSerializers(supervisor, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Supervisor updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            supervisor = self.get_supervisor(pk)

            supervisor.delete()
            return Response({"message": "Supervisor deleted successfully"}, status=status.HTTP_200_OK)
                            
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ShippingCreateView(BaseTokenView):
    
    def get_customer(self,pk):
        return get_object_or_404(Customers,pk=pk)
    
    def post(self, request,pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            customer = self.get_customer(pk)
            
            serializer = ShippingSerializers(data=request.data,context={'created_user':authUser}) 
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Shipping Address Add successfully", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self, request,pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            customer = self.get_customer(pk)
            
            shipping = Shipping.objects.filter(customer=customer)
            serializer = ShippingAddressView(shipping, many=True)
            return Response({"message": "Shipping Address List successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        



            
            
class CustomerShippingAddressUpdate(BaseTokenView):
    def shipping_address(self,pk):
        return get_object_or_404(Shipping,pk=pk)
    
    def get(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            address = self.shipping_address(pk)
            serializer = ShippingSerializers(address)
            return Response({"message": "Address fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
                            
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request,pk):
        try:
            tauthUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            address = self.shipping_address(pk)
            address.delete()
            return Response({"message": "Customer address deleted successfully"}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def put(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            address = self.shipping_address(pk)
            serializer = ShippingSerializers(address, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "address updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



import json
import itertools

class VariantProductCreate(BaseTokenView):
    def post(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            # Get request data
            product_id = request.data.get("product")
            attributes = request.data.get("attributes", "[]")

            try:
                attributes = json.loads(attributes) 
            except json.JSONDecodeError:
                return Response({"message": "Invalid attributes format"}, status=status.HTTP_400_BAD_REQUEST)

            images = request.FILES.getlist('images')

            # Fetch product
            product_instance = Products.objects.filter(pk=product_id).first()
            if not product_instance:
                return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

            # Get the existing product's family
            existing_family = product_instance.family.all()  # Retrieve the product's existing family

            # Process attributes for variants
            if product_instance.type == "variant":
                attribute_values = {}
                for attr in attributes:
                    attr_name = attr.get("attribute")
                    attr_values_list = attr.get("values", [])

                    if not isinstance(attr_values_list, list):
                        return Response({"message": "Attribute values must be a list"}, status=status.HTTP_400_BAD_REQUEST)

                    attribute_values[attr_name] = attr_values_list

                combinations = list(itertools.product(*attribute_values.values()))

                for combination in combinations:
                    combined_attr = dict(zip(attribute_values.keys(), combination))

                    all_attributes = '-'.join(combination)  

                    # Create the variant name based on attributes
                    name = f"{product_instance.name}-{'-'.join(combination)}"

                    # Initialize values for color and size based on attribute names
                    color = None
                    size = None

                    # The first attribute value will be assigned to color, and the second to size
                    # Assign the first value to color
                    if combined_attr:
                        color = combination[0]  # First attribute value for color
                    # Assign the second value to size
                    if len(combination) > 1:
                        size = combination[1]  # Second attribute value for size

                    # Create the variant product with the same family
                    variant_product = Products.objects.create(
                        created_user=User.objects.get(pk=authUser.pk),
                        name=name,
                        type="variant",
                        unit=product_instance.unit,
                        purchase_rate=product_instance.purchase_rate,
                        tax=product_instance.tax,
                        exclude_price=product_instance.exclude_price,
                        selling_price=product_instance.selling_price,
                        stock=product_instance.stock,
                        color=color,
                        size=size,
                        groupID=product_instance.groupID,
                    )

                    # Add the existing family to the variant product using set()
                    variant_product.family.set(existing_family)

            else:
                # If it's not a variant, just handle the image uploads
                for image in images:
                    SingleProducts.objects.create(
                        product=product_instance,
                        created_user=User.objects.get(pk=authUser.pk),
                        image=image
                    )

            return Response({"message": "Product added successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}", exc_info=True)
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class VariantProductsByProductView(BaseTokenView):
    def get(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            product = get_object_or_404(Products,pk=pk)
            serializer = ProductSerializerView(product)
            return Response({"products": serializer.data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "status": "error",
                "message": "An error occurred",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        

    

class CreateOrder(BaseTokenView):
    def post(self, request):
        try:
            # Authenticate user
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            # Retrieve cart items and validate serializer
            cart_items = BeposoftCart.objects.filter(user=authUser)
            serializer = OrderSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({"status": "error", "message": "Validation failed", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            order = serializer.save()  # Create order
            
            for item_data in cart_items:
                product = get_object_or_404(Products, pk=item_data.product.pk)

                # Convert values to Decimal for consistency
                quantity = Decimal(item_data.quantity)
                selling_price = Decimal(item_data.product.selling_price)
                discount = Decimal(item_data.discount or 0)
                tax = Decimal(item_data.product.tax or 0)
                rate = Decimal(item_data.product.selling_price or 0)

                

                # Check stock and decrement
              
                if product.stock < quantity:
                    return Response({"status": "error", "message": "Insufficient stock for single product"}, status=status.HTTP_400_BAD_REQUEST)
                product.stock -= int(quantity)
                product.save()
                

                # Create order item for each valid cart item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    variant=item_data.variant,
                    size=item_data.size if item_data.size else None,
                    quantity=int(quantity),
                    discount=discount,
                    tax=tax,
                    rate=rate,
                    description=item_data.note,
                )
            
            # Clear cart after successful order creation
            cart_items.delete()
            return Response({"status": "success", "message": "Order created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.info(f"Order Creating error is   {e}")
            return Response({"status": "error", "message": "An unexpected error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderListView(BaseTokenView):
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            orders = Order.objects.all()
            serializer = OrderModelSerilizer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Orders not found"}, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError:
            return Response({"status": "error", "message": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

        


class CustomerOrderItems(BaseTokenView):
    def get(self, request, order_id):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
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
        



logger = logging.getLogger(__name__)

class CustomerOrderStatusUpdate(BaseTokenView):
    def put(self, request, pk):
        authUser, error_response = self.get_user_from_token(request)
        if error_response:
            return error_response

        try:
            order = Order.objects.filter(pk=pk).first()
            if not order:
                return Response({"status": "error", "message": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

            # Extract new status from request data
            new_status = request.data.get('status')
            if not new_status:
                return Response({"status": "error", "message": "Status field is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Update the order status
            order.status = new_status
            order.save()

            return Response({"status": "success", "message": "Order status updated successfully"}, status=status.HTTP_200_OK)

        except DatabaseError:
            return Response({"status": "error", "message": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class ShippingManagementView(BaseTokenView):
    def put(self,request,pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            order = Order.objects.filter(pk=pk).first()
            if not order:
                return Response({"status": "error", "message": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = OrderSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success", "message": "Order updated successfully"}, status=status.HTTP_200_OK)
            return Response({"status": "error", "message": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)
        
        except DatabaseError:
            return Response({"status": "error", "message": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

        

class ProductAttributeCreate(BaseTokenView):
    def  post(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            serializer = AttributesModelSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(created_user = authUser)
                return Response({"status": "success", "message": "Product attribute created successfully"}, status=status.HTTP_201_CREATED)
            return Response({"status": "error", "message": "Invalid data", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
            

class ProductAttributeListView(BaseTokenView):
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            attributes = Attributes.objects.all()
            serializer = AttributesModelSerializer(attributes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except DatabaseError:
            return Response({"status": "error", "message": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class ProductAttributeView(BaseTokenView):

    def get_user_and_attribute(self, request, pk):
        authUser, error_response = self.get_user_from_token(request)
        if error_response:
            return None, error_response

        attribute = get_object_or_404(Attributes, pk=pk)
        return attribute, None

    def put(self, request, pk):
        attribute, error_response = self.get_user_and_attribute(request, pk)
        if error_response:
            return error_response

        serializer = AttributesModelSerializer(attribute, data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({"status": "success", "message": "Attribute updated successfully"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        attribute, error_response = self.get_user_and_attribute(request, pk)
        if error_response:
            return error_response
        try:
            attribute.delete()
            return Response({"status": "success", "message": "Attribute deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



logger = logging.getLogger(__name__)

class ProductAttributeCreateValue(BaseTokenView):
    def post(self, request):
        authUser, error_response = self.get_user_from_token(request)
        if error_response:
            return error_response

        serializer = ProductAttributeModelSerilizer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Attribute value created successfully: {serializer.data}")
            return Response({"status": "success", "message": "Attribute value created successfully"}, status=status.HTTP_201_CREATED)
        return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            attributes_values = ProductAttribute.objects.all()
            serializer = ProductAttributeModelSerilizer(attributes_values, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e :
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


            
        


class ProductAttributeListValue(BaseTokenView):
    def get(self,request,pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            attributes_values = ProductAttribute.objects.filter(attribute=pk)
            serializer = ProductAttributeModelSerilizer(attributes_values, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Attribute not found"}, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError:
            return Response({"status": "error", "message": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class ProductAttributeValueDelete(APIView):
    def delete(self, request, pk):
        try:
            attribute_value = ProductAttribute.objects.filter(pk=pk).first()
            if not attribute_value:
                return Response({"status": "error", "message": "Attribute value not found"}, status=status.HTTP_404_NOT_FOUND)
            
            attribute_value.delete()
            return Response({"status": "success", "message": "Attribute value deleted"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"status": "error", "message": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class StaffCustomersView(BaseTokenView):
    def get(self,request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            customers = Customers.objects.filter(manager = authUser)
            if not customers:
                return Response({"status": "error", "message": "No customers found"}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = CustomerModelSerializer(customers, many=True)
            return Response({"data":serializer.data}, status=status.HTTP_200_OK)
        
        except Exception as e :
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        

class Cart(BaseTokenView):
    PRODUCT_TYPE_SINGLE = 'single'
    
    def post(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            product = get_object_or_404(Products, pk=request.data.get("product"))
            quantity = request.data.get("quantity")
            
            return self.add_product_in_cart(product, quantity, authUser)
           
        except KeyError as e:
            return Response({"status": "error", "message": f"Missing field: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_product_in_cart(self, product, quantity, user):
        BeposoftCart.objects.create(product=product, user=user, quantity=quantity)
        return Response({"status": "success", "message": "Product added to cart"}, status=status.HTTP_201_CREATED)


    



class StaffDeleteCartProduct(BaseTokenView):
    
    def put(self,request,pk):
        try :

            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            

            cartItem = get_object_or_404(BeposoftCart, pk=pk)
            serializer = BepocartSerializers(cartItem, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success", "message": "Cart item updated successfully."}, status=status.HTTP_200_OK)
            return Response({"status" : "error","message":serializer.errors}, status=status.HTTP_200_OK)
        
        except Exception as e :
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, pk):
        try:
            # Authenticate user from token
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            cartItem = get_object_or_404(BeposoftCart, pk=pk)
            cartItem.delete()
            return Response({"status": "success", "message": "Cart item deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            # Handle exceptions and return error response
            return Response({"status": "error", "message": "An error occurred while deleting the cart item.", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
    

class StaffcartStoredProductsView(BaseTokenView):
    def get(self,request):
        try :
        
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            staffItems = BeposoftCart.objects.filter(user = authUser)
            serializers = BepocartSerializersView(staffItems, many=True)
            return Response({"data":serializers.data},status=status.HTTP_200_OK)
        
        except Exception as  e :
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
        
class CreateBankAccountView(BaseTokenView):
    def post(self, request):
        try:
            # Authenticate the user
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            data = request.data
            if isinstance(data, dict):
                data = [data]
            
            if not isinstance(data, list):
                return Response(
                    {"status": "error", "message": "Invalid data format. Must be a dictionary or list of dictionaries."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = BankSerializer(data=data, many=True)
            if serializer.is_valid():
                serializer.save(created_user=authUser)
                return Response(
                    {"status": "success", "message": "Bank account(s) created successfully."},
                    status=status.HTTP_201_CREATED,
                )
            
            return Response(
                {"status": "error", "message": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": "An error occurred", "errors": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        
class BankView(BaseTokenView):
    def get(self,request):
        try :
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            banks = Bank.objects.all()
            serializer = BankSerializer(banks, many=True)
            return Response({"data":serializer.data},status=status.HTTP_200_OK)
        except Exception as  e :
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class BankAccountView(BaseTokenView):
    def get(self,request):
        try :
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            bankAccount = Bank.objects.filter(user = authUser)
            serializer = BankSerializer(bankAccount, many=True)
            return Response({"data":serializer.data},status=status.HTTP_200_OK)
        except Exception as  e :
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self,request,pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            bank = get_object_or_404(Bank, pk=pk)
            serializer = BankSerializer(bank, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success"}, status=status.HTTP_200_OK)
            return Response({"error":serializer.errors})
        except Exception as e :
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
class ExistedOrderAddProducts(BaseTokenView):
    
    def post(self, request, pk):
        try:
            
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            # Retrieve the order instance using the primary key (pk)
            order = get_object_or_404(Order, pk=pk)
          
            product = get_object_or_404(Products, pk=request.data.get("product"))
            quantity = request.data.get("quantity")
            if quantity is None:
                return Response({"status": "error", "message": "Quantity is required."}, status=status.HTTP_400_BAD_REQUEST)

            

            return self.add_single_product_to_cart(product, order, quantity)
        
        except KeyError as e:
            return Response({"status": "error", "message": f"Missing field: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_single_product_to_cart(self, product, order, quantity):
        """Add a single product to the cart."""
        OrderItem.objects.create(
            product=product,            # Pass the Product instance
            rate=product.selling_price,  # Set rate based on product
            order=order,                 # Pass the Order instance directly
            quantity=quantity,
            tax = product.tax,
        )
        return Response({"status": "success", "message": "Product added to cart"}, status=status.HTTP_201_CREATED)
        
    
class RemoveExistsOrderItems(BaseTokenView):
    
    def get_order_item(self, pk):
        try:
            order_item = get_object_or_404(OrderItem, pk=pk)

            return order_item
        except OrderItem.DoesNotExist:
            return None
    def delete(self,request,pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            order_item = self.get_order_item(pk)
            if not order_item:
                return Response({"status": "error", "message": "Order item not found"}, status=status.HTTP_404_NOT_FOUND)
            order_item.delete()
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        except Exception as e :
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
                        
            item = self.get_order_item(pk)
            if not item:
                return Response({"status": "error", "message": "Order item not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = ExistedOrderAddProductsSerializer(item, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success", "message": "Order item updated successfully"}, status=status.HTTP_200_OK)
            return Response({"status": "error", "message": "Invalid data provided"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e :
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderTotalAmountSave(BaseTokenView):
    def put(self,request,pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            order = get_object_or_404(Order, pk=pk)
            serializer = OrderSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success", "message": "Order updated successfully"}, status=status.HTTP_200_OK)
            return Response({"status": "error", "message": "Invalid data provided"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e :
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
        
class CreateReceiptAgainstInvoice(BaseTokenView):
    def post(self, request, pk):
        try:
            # Authenticate user from token
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            order = get_object_or_404(Order, pk=pk)
            
            request.data['order'] = order.pk
            request.data['customer'] = order.customer.pk
            request.data['created_by'] = authUser.pk
            
            serializer = PaymentRecieptSerializers(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success", "message": "Receipt created successfully"}, status=status.HTTP_200_OK)

         
            return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Log the exception message for debugging
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class CustomerOrderLedgerdata(BaseTokenView):
    def get(self,request,pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            customer = get_object_or_404(Customers, pk=pk)
            ledger = Order.objects.filter(customer =customer.pk)
            
            serializers = LedgerSerializers(ledger, many=True)
            return Response({"data":serializers.data},status=status.HTTP_200_OK)
        except Exception as e :
            return Response({"errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
            
            


class CreatePerfomaInvoice(BaseTokenView):
    def post(self, request):
        try:
            # Authenticate user
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            # Retrieve cart items and validate serializer
            cart_items = BeposoftCart.objects.filter(user=authUser)
            serializer = PerfomaInvoiceOrderSerializers(data=request.data)
            if not serializer.is_valid():
                return Response({"status": "error", "message": "Validation failed", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            order = serializer.save()  # Create order
            
            for item_data in cart_items:
                product = get_object_or_404(Products, pk=item_data.product.pk)

                # Convert values to Decimal for consistency
                quantity = Decimal(item_data.quantity)
                selling_price = Decimal(item_data.product.selling_price)
                discount = Decimal(item_data.discount or 0)
                tax = Decimal(item_data.product.tax or 0)
                rate = Decimal(item_data.product.selling_price or 0)

                

                # Check stock and decrement
                if product.stock < quantity:
                    return Response({"status": "error", "message": "Insufficient stock for single product"}, status=status.HTTP_400_BAD_REQUEST)
                product.stock -= int(quantity)
                product.save()
            
               

                # Create order item for each valid cart item
                PerfomaInvoiceOrderItem.objects.create(
                    order=order,
                    product=product,
                    variant=item_data.variant,
                    size=item_data.size,
                    quantity=int(quantity),
                    discount=discount,
                    tax=tax,
                    rate=rate,
                    description=item_data.note,
                )
            
            # Clear cart after successful order creation
            cart_items.delete()
            return Response({"status": "success", "message": "Order created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error("Unexpected error in CreateOrder view: %s", str(e))
            return Response({"status": "error", "message": "An unexpected error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PerfomaInvoiceListView(BaseTokenView):
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            orders = PerfomaInvoiceOrder.objects.all()
            serializer = PerfomaInvoiceProductsSerializers(orders, many=True)
            return Response({"data":serializer.data}, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Orders not found"}, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError:
            return Response({"status": "error", "message": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class PerfomaInvoiceDetailView(BaseTokenView):
    def get(self, request, invoice):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            perfoma = PerfomaInvoiceOrder.objects.filter(invoice=invoice).first()
            if not perfoma:
                return Response({"status": "error", "message": "Order not found"}, status=status.HTTP_204_NO_CONTENT)
            
            serializer = PerfomaInvoiceProductsSerializers(perfoma)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class CreateCompnayDetailsView(BaseTokenView):
    def post(self, request):
        try:
            # Authenticate the user
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            # Check if the incoming data is single or multiple
            data = request.data
            if isinstance(data, dict):
                # Single record: Wrap it in a list to reuse the bulk handling logic
                data = [data]
            
            if not isinstance(data, list):
                return Response(
                    {"status": "error", "message": "Invalid data format. Must be a dictionary or list of dictionaries."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Pass user to the serializer context
            serializer = CompanyDetailsSerializer(data=data, many=True, context={'user': authUser})
            if serializer.is_valid():
                serializer.save()  # Handles both single and multiple
                return Response(
                    {"status": "success", "message": "Company details created successfully"},
                    status=status.HTTP_201_CREATED,
                )
            
            # Return validation errors
            return Response(
                {"status": "error", "message": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            company = Company.objects.all()
            serializer = CompanyDetailsSerializer(company, many=True)
            return Response(
                    {"data": serializer.data,"status":"success"},
                    status=status.HTTP_200_OK,
                )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        


class WarehouseDataView(BaseTokenView):
    def post(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            if isinstance(request.data, list):
                serializer = WarehouseBoxesDataSerializer(data=request.data, many=True)
            else:
                serializer = WarehouseBoxesDataSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response({"status":"success","data":serializer.data}, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            data = Warehousedata.objects.all()
            serializer = WarehouseBoxesDataSerializer(data, many=True)
            return Response({"data":serializer.data,"status":"success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
class WarehouseDetailView(BaseTokenView):
    def put(self,request,pk):
        try:
            authUser,error_response=self.get_user_from_token(request)  
            if error_response:
                return error_response
            warehousedata = get_object_or_404(Warehousedata,pk=pk)
            serializer = WarehouseUpdateSerializers(warehousedata, data=request.data,partial =True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def delete(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            warehousedata = get_object_or_404(Warehousedata, pk=pk)
            warehousedata.delete()
            return Response({"status": "success", "message": "Warehouse data deleted"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                            
       
class DailyGoodsView(BaseTokenView):
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            warehouse=Warehousedata.objects.all()
            
            seen_dates = set()
            response_data=[]
        
            for box_detail in warehouse:
               
                if box_detail.shipped_date not in seen_dates:
                    boxes_for_date = warehouse.filter(shipped_date=box_detail.shipped_date)
                    total_weight = 0
                    for box in boxes_for_date:
                        try:
                            total_weight += float(box.weight)


                        except (ValueError, TypeError):
                            continue 

                    # Calculate total volume weight
                    total_volume_weight = 0
                    for box in boxes_for_date:
                        try:
                            length = float(box.length)
                            breadth = float(box.breadth)
                            height = float(box.height)
                            total_volume_weight += (length * breadth * height) / 6000
                        except (ValueError, TypeError):
                            continue 
                    total_shipping_charge =0  
                    for box in boxes_for_date:
                        try:
                            total_shipping_charge += float(box.shipping_charge)
                        except (ValueError, TypeError):
                            continue
                    total_boxes = boxes_for_date.count()    

                    # Serialize the boxes for the date
                    serializer = WarehousedataSerializer(boxes_for_date, many=True)
                

                    # Add the data for the current shipped_date
                    response_data.append({
                        "shipped_date": box_detail.shipped_date,
                        "total_boxes":total_boxes,

                        "total_weight": round(total_weight, 2),
                        "total_volume_weight": round(total_volume_weight, 2),
                        "total_shipping_charge":round(total_shipping_charge,2)          #shipping_charge=delivery_charge
                        # "boxes": serializer.data
                    })

                    seen_dates.add(box_detail.shipped_date)

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
         
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DailyGoodsBydate(BaseTokenView):
    def get(self,request,date):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
      
            warehouse_data = Warehousedata.objects.filter(shipped_date=date)
            if not warehouse_data.exists():
                return Response({"Order Not Found"})
            serializer = WarehousedataSerializer(warehouse_data, many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ExpensAddView(BaseTokenView):
    def post(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            expense=ExpenseSerializer(data=request.data)
            if expense.is_valid():
                expense.save()
                return Response({"status": "success", "message": "Expense Added Successfully","data":expense.data}, status=status.HTTP_200_OK)
            return Response(expense.errors,status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            expense_data = ExpenseModel.objects.all()
            serializer = ExpenseModelsSerializers(expense_data, many=True)
            return Response({"data":serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ExpenseUpdate(BaseTokenView):
    def put(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            expense=get_object_or_404(ExpenseModel,pk=pk)
            serializer = ExpenseSerializer(expense, data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success", "message": "Expense Updated Successfully"}, status=status.HTTP_200_OK)
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                            
        


class GRVaddView(BaseTokenView):
    def post(self, request):
        try:
            # Authenticate the user using the token
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            # Ensure the request data is a list of dictionaries
            data = request.data if isinstance(request.data, list) else [request.data]

            # Use the serializer with `many=True` for lists
            grvdata = GRVModelSerializer(data=data, many=True)

            # Validate and save the data
            if grvdata.is_valid():
                grvdata.save()
                return Response({
                    "status": "success",
                    "message": "Added successfully",
                    "data": grvdata.data
                }, status=status.HTTP_200_OK)

            logger.error(f"Validation failed: {grvdata.errors}")
            return Response({
                "status": "error",
                "message": "Validation failed",
                "errors": grvdata.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error occurred in GRVaddView: {str(e)}")
            return Response({
                "status": "error",
                "message": "An error occurred while processing the request",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self,request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
           
            grvdata = GRVModel.objects.all()

            if not grvdata.exists():
                return Response(
                    {"status": "error", "message": "No GRV records found for this staff."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Serialize the GRV data
            serializer = GRVSerializer(grvdata, many=True)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
          
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        


class GRVGetViewById(BaseTokenView):
    def get(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            grvs=GRVModel.objects.get(pk=pk)
            serializer = GRVModelSerializer(grvs)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            


class GRVUpdateView(BaseTokenView):
    
    def put(self, request,pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            grv = get_object_or_404(GRVModel, pk=pk)
            grvdata = GRVModelSerializer(grv, data=request.data,partial=True)
            if grvdata.is_valid():
                grvdata.save()
                
                return Response({"status": "success", "message": "GRV updated successfully"}, status=status.HTTP_200_OK)
            return Response(grvdata.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
            
        
                

            


class SalesReportView(BaseTokenView):
    def get(self, request):
        try:
            # Assuming get_user_from_token is a method that retrieves the user from a token
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            # Fetch all orders
            orders = Order.objects.all()

            # Approved order statuses
            approved_statuses = [
                'Approved', 
                'Shipped', 
                'Invoice Created', 
                'Invoice Approved', 
                'Waiting For Confirmation',
                'Invoice Rejected',  # Typo fixed from 'Rejectd'
                'To Print', 
                'Processing', 
                'Completed'
            ]

            # Get distinct dates for orders
            distinct_dates = orders.values_list('order_date', flat=True).distinct()

            # Prepare the report data
            report_data = []

            for date in distinct_dates:
                daily_orders = orders.filter(order_date=date)
                total_amount = daily_orders.aggregate(total=Sum('total_amount'))['total'] or 0
                total_bills = daily_orders.count()

                # Approved orders
                approved_bills = daily_orders.filter(status__in=approved_statuses)
                approved_count = approved_bills.count()
                approved_amount = approved_bills.aggregate(total=Sum('total_amount'))['total'] or 0

                # Rejected orders
                rejected_bills = daily_orders.exclude(status__in=approved_statuses)
                rejected_count = rejected_bills.count()
                rejected_amount = rejected_bills.aggregate(total=Sum('total_amount'))['total'] or 0

                # Order details for the current date
                order_details = daily_orders.values('id','invoice', 'order_date', 'status', 'total_amount', 'customer__name', 'manage_staff__name','company__name','state__name','family__name')

                report_data.append({
                    "date": date,
                    "total_bills_in_date": total_bills,
                    "amount": total_amount,
                    "approved": {
                        "bills": approved_count,
                        "amount": approved_amount,
                    },
                    "rejected": {
                        "bills": rejected_count,
                        "amount": rejected_amount,
                    },
                    "order_details": list(order_details), 
                })

            return Response({"sales_report": report_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        

class InvoiceReportView(BaseTokenView):
    def get(self, request, date):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            # Parse and validate the date
            date = parse_date(date)
            if not date:
                return Response(
                    {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."},
                    status=400
                )

            # Filter orders for the given date
            orders = Order.objects.filter(order_date=date)

            # Get staff details and their order counts
            staff_ids = orders.values_list('manage_staff', flat=True).distinct()
            staff_details = User.objects.filter(id__in=staff_ids)

            staff_info = []
            for staff in staff_details:
                # Fetch total orders handled by this staff
                staff_orders = orders.filter(manage_staff=staff)

                # Collect detailed information for all orders handled by this staff
                staff_orders_details = []
                for order in staff_orders:
                    try:
                        staff_orders_details.append({
                            'invoice': order.invoice,
                            'status': order.status,
                            'company': order.company.name if order.company else None,
                            'customer': order.customer.name if order.customer else None,
                            'state': order.state.name if order.state else None,
                            'total_amount': order.total_amount,
                            'order_date': order.order_date,
                            'family_name': order.family.name if order.family else None
                        })
                    except AttributeError as e:
                        print(f"Error processing order {order.pk}: {e}")
                        raise

                staff_info.append({
                    'id': staff.pk,
                    'name': staff.name,
                    'family': staff.family.name if staff.family else None,
                    'orders_details': staff_orders_details
                })

            return Response({
                "status": "success",
                "data": staff_info,
            })

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)



        
class BillsView(BaseTokenView):
    def get(self,request,pk,date):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            order_list=Order.objects.filter(order_date = date, manage_staff = pk)
            serializer = OrderSerializer(order_list, many=True)
            return Response({"data":serializer.data})
          

        except Exception as e :
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CreditSalesReportView(BaseTokenView):
    def get(self, request):
        try:
                   
            
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            # Fetch all orders with 'credit' payment status
            orders = Order.objects.filter(payment_status="credit")
            
            # Count the total number of orders
            bills = orders.count()

            # Initialize a dictionary to store total amount per unique order date
            total_by_date = {}

            # Loop through the orders to accumulate total amounts by order date
            for order in orders:
                order_date = order.order_date
                
                # If the order date is not already in the dictionary, initialize it
                if order_date not in total_by_date:
                    total_by_date[order_date] = {
                        'total_amount': 0, 
                        'total_orders': 0, 
                        'total_paid': 0, 
                        'total_pending': 0
                    }

                # Accumulate the total amount and total orders
                total_by_date[order_date]['total_amount'] += order.total_amount
                total_by_date[order_date]['total_orders'] += 1

                # Get the paid amount from PaymentReceipt (sum of the amount field)
                paid_amount = PaymentReceipt.objects.filter(order=order).aggregate(total_paid=Sum('amount'))['total_paid']
                
                # If no payment receipts, set the paid amount to 0
                paid_amount = paid_amount if paid_amount is not None else 0
                
                # Accumulate the paid amount
                total_by_date[order_date]['total_paid'] += paid_amount

                # Calculate pending amount (total_amount - total_paid)
                pending_amount = order.total_amount - paid_amount
                total_by_date[order_date]['total_pending'] += pending_amount

            # Prepare the response data
            response_data = [
                {
                "date": date,
                    "total_amount": data['total_amount'],
                    "total_orders": data['total_orders'],
                    "total_paid": data['total_paid'],
                    "total_pending": data['total_pending']
                }
                for date, data in total_by_date.items()

                
            ]

            # Return the response with the order summary
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
          
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CreditBillsView(BaseTokenView):
    def get(self,request,date):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            order_list=Order.objects.filter(order_date =date,payment_status="credit")
            serializer = OrderPaymentSerializer(order_list, many=True)
            return Response({"data":serializer.data})
          

        except Exception as e :
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CODSalesReportView(BaseTokenView):
    
    def get(self, request):
        try:
                   
            
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            # Fetch all orders with 'credit' payment status
            orders = Order.objects.filter(payment_status="COD")
            
            # Count the total number of orders
            bills = orders.count()

            # Initialize a dictionary to store total amount per unique order date
            total_by_date = {}

            # Loop through the orders to accumulate total amounts by order date
            for order in orders:
                order_date = order.order_date
                
                # If the order date is not already in the dictionary, initialize it
                if order_date not in total_by_date:
                    total_by_date[order_date] = {
                        'total_amount': 0, 
                        'total_orders': 0, 
                        'total_paid': 0, 
                        'total_pending': 0
                    }

                # Accumulate the total amount and total orders
                total_by_date[order_date]['total_amount'] += order.total_amount
                total_by_date[order_date]['total_orders'] += 1

                # Get the paid amount from PaymentReceipt (sum of the amount field)
                paid_amount = PaymentReceipt.objects.filter(order=order).aggregate(total_paid=Sum('amount'))['total_paid']
                
                # If no payment receipts, set the paid amount to 0
                paid_amount = paid_amount if paid_amount is not None else 0
                
                # Accumulate the paid amount
                total_by_date[order_date]['total_paid'] += paid_amount

                # Calculate pending amount (total_amount - total_paid)
                pending_amount = order.total_amount - paid_amount
                total_by_date[order_date]['total_pending'] += pending_amount

            # Prepare the response data
            response_data = [
                {
                "date": date,
                    "total_amount": data['total_amount'],
                    "total_orders": data['total_orders'],
                    "total_paid": data['total_paid'],
                    "total_pending": data['total_pending']
                }
                for date, data in total_by_date.items()

                
            ]

            # Return the response with the order summary
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


class CODBillsView(BaseTokenView):
    def get(self,request,date):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            order_list=Order.objects.filter(order_date =date,payment_status="COD")
            serializer = OrderPaymentSerializer(order_list, many=True)
            return Response({"data":serializer.data})
          

        except Exception as e :
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                


        
            
    

class ProductSalesReportView(APIView):
    def get(self, request):
        try:
            # Fetch all order items with related product and order details
            order_items = OrderItem.objects.select_related('product', 'order').all()

            if not order_items.exists():
                return Response(
                    {"error": "No records found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Group order items by date and product
            grouped_data = defaultdict(lambda: defaultdict(list))

            for item in order_items:
                # Parse `order_date`
                date = item.order.order_date
                formatted_date = (
                    date if isinstance(date, str) else date.strftime('%Y-%m-%d')
                )

                product_name = item.product.name

                # Serialize individual order items
                serializer = ProductSalesReportSerializer(item)
                grouped_data[formatted_date][product_name].append(serializer.data)

            # Fetch remaining stock directly from the Products model
            product_stock = {
                product.name: product.stock for product in Products.objects.all()
            }

            # Format the final response
            formatted_response = []
            for date, products in grouped_data.items():
                for product, data in products.items():
                    formatted_response.append({
                        "date": date,
                        "product": product,
                        "stock": product_stock.get(product, 0),  # Attach stock from Products model
                        "data": data
                    })

            return Response(formatted_response, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        
        


        


class StatewiseSalesReport(APIView):
    def get(self, request):
        try:
            states = State.objects.all()
            data = []

            for state in states:
                # Get orders grouped by order_date for the state
                orders_by_date = Order.objects.filter(state=state).values('order_date').distinct()

                # Calculating counts and total amounts for each status
                total_orders = Order.objects.filter(state=state).count()
                total_amount = Order.objects.filter(state=state).aggregate(total=Sum('total_amount'))['total'] or 0

                approved_orders = Order.objects.filter(state=state, status='Approved').count()
                approved_amount = Order.objects.filter(state=state, status='Approved').aggregate(total=Sum('total_amount'))['total'] or 0

                shipped_orders = Order.objects.filter(state=state, status='Completed').count()
                shipped_amount = Order.objects.filter(state=state, status='Completed').aggregate(total=Sum('total_amount'))['total'] or 0

                cancelled_orders = Order.objects.filter(state=state, status='Cancelled').count()
                cancelled_amount = Order.objects.filter(state=state, status='Cancelled').aggregate(total=Sum('total_amount'))['total'] or 0

                rejected_orders = Order.objects.filter(state=state, status='Rejected').count()
                rejected_amount = Order.objects.filter(state=state, status='Rejected').aggregate(total=Sum('total_amount'))['total'] or 0

                returned_orders = Order.objects.filter(state=state, status='Return').count()
                returned_amount = Order.objects.filter(state=state, status='Return').aggregate(total=Sum('total_amount'))['total'] or 0

                state_data = {
                    'id': state.pk,
                    'name': state.name,
                    'total_orders_count': total_orders,
                    'total_amount': total_amount,
                    'approved_orders_count': approved_orders,
                    'approved_amount': approved_amount,
                    'completed_orders_count': shipped_orders,
                    'completed_amount': shipped_amount,
                    'cancelled_orders_count': cancelled_orders,
                    'cancelled_amount': cancelled_amount,
                    'rejected_orders_count': rejected_orders,
                    'rejected_amount': rejected_amount,
                    'returned_orders_count': returned_orders,
                    'returned_amount': returned_amount,
                    'orders': []
                }

                for order_date in orders_by_date:
                    date_orders = Order.objects.filter(state=state, order_date=order_date['order_date'])
                    order_data = {
                        'order_date': order_date['order_date'],
                        'waiting_orders': OrderModelSerilizer(date_orders, many=True).data
                    }
                    state_data['orders'].append(order_data)

                data.append(state_data)

            return Response({"data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class StateOrderDetailsView(BaseTokenView):
    def get(self, request, state_id):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

           
            state = State.objects.get(pk=state_id)
            
            orders = Order.objects.filter(state=state)

            serializer = OrderDetailSerializer(orders, many=True)

           
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)

        except State.DoesNotExist:
            return Response({"status": "error", "message": "State not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
          
            return JsonResponse({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class DeliveryListView(BaseTokenView):
    def get(self, request,date):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            data=Warehousedata.objects.filter(shipped_date=date)
            serializer=WareHouseSerializer(data, many=True)
            return Response({"data":serializer.data},status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
        


class ParcalServiceView(BaseTokenView):
    def post(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            serializer = ParcalSerializers(data = request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success", "message": "Parcal saved successfully"}, status=status.HTTP_200_OK)
            return Response({"status":"error","message":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e :
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self, request):
        try:
            parcal = ParcalService.objects.all()
            serializer = ParcalSerializers(parcal, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
class EditParcalService(APIView):
    def put(self, request, pk):
        try:
            parcal = ParcalService.objects.get(pk=pk)
            serializer = ParcalSerializers(parcal, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success", "message": "Parcal updated successfully"}, status=status.HTTP_200_OK)
            return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e :
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
