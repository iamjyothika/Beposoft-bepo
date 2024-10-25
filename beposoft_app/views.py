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
            user, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            allocated_states = request.data.getlist('allocated_states', [])
            print(f"Allocated States Received: {allocated_states}") 
            
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                print("Response data    :",serializer.data)
                return Response({"data": serializer.data, "message": "User created successfully"}, status=status.HTTP_201_CREATED)
            print(serializer.errors)
            return Response({"status": "error", "message": "Validation failed","errors": serializer.errors }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({ "status": "error", "message": "An error occurred","errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



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
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            user = self.get_user(pk)
            
            allocated_states = request.data.getlist('allocated_states', [])
            print(f"Allocated States Received: {allocated_states}") 
            
            # If the password is provided, hash it
            if 'password' in request.data:
                request.data['password'] = make_password(request.data['password'])
                
            serializer = UserUpdateSerilizers(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "User updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
            print(serializer.errors)
            return Response({"status": "error", "message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class UserCustomerAddingView(BaseTokenView):
    def post(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            serializer = CustomerModelSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"data": serializer.data, "message": "Customer added successfully"}, status=status.HTTP_201_CREATED)
            print(serializer.errors)
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
    def post(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            # Retrieve family IDs from request data
            family_ids = request.data.getlist('family[]')  # Use the same key as in FormData

            # Check if family_ids is not empty
            if not family_ids:
                return Response({"message": "No family IDs provided"}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve Family instances based on the provided IDs
            families = Family.objects.filter(pk__in=family_ids)

            # Ensure at least one family is found
            if not families.exists():
                return Response({"message": "No valid family IDs provided"}, status=status.HTTP_400_BAD_REQUEST)

            # Initialize serializer with request data
            serializer = ProductsSerializer(data=request.data)
            
            if serializer.is_valid():
                # Save the product instance
                product = serializer.save()

                # Associate the product with the selected families
                product.family.set(families)  # Assuming `family` is a ManyToMany field in your Product model
                
                print(f"Save Data: {serializer.data}")
                return Response({"message": "Product added successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
            print(f"{serializer.errors}")
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error occurred while creating a product: {str(e)}")
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProductListView(BaseTokenView):
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            product = Products.objects.all()
            serializer = ProductSerializerView(product, many=True)
            return Response({"message": "Product list successfully retrieved", "data": serializer.data}, status=status.HTTP_200_OK)
                        
        except authUser.DoesNotExist:
            return Response({"status": "error", "message": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




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
        



class SingleProductImageCreateview(BaseTokenView):
    def post(self, request, pk):
        try:
            # Get authenticated user
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            # Get the product
            product = Products.objects.get(pk=pk)

            # Get the list of images from the request
            images = request.FILES.getlist('images')
            if not images:
                return Response({"message": "No images were uploaded"}, status=status.HTTP_400_BAD_REQUEST)

            print(f"images   :{images}")  # Debugging log

            # Process and save all images
            saved_images = []  # For tracking the saved images
            for image in images:
                single_product = SingleProducts.objects.create(product=product, created_user=authUser, image=image)
                saved_images.append(single_product)

            # If all images are processed, return a success message
            return Response({
                "message": f"{len(saved_images)} images added successfully",
                "saved_images": [img.id for img in saved_images]  # Return IDs of saved images
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            print(f"Error: {e}")  # Print error for debugging
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            

class SingleProductImageView(BaseTokenView):
    def delete(self,request,pk):
        try :
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            image = SingleProducts.objects.get(pk=pk)
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
            print(serializer.errors)
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

            serializer = StateSerializers(data=request.data)
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
            print(serializer.errors)
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
            print(serializer.errors)
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
            print(serializer.errors)
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e)
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


import json

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
            print(attributes)

            try:
                attributes = json.loads(attributes) 
            except json.JSONDecodeError:
                print("invalid atribute format")
                return Response({"message": "Invalid attributes format"}, status=status.HTTP_400_BAD_REQUEST)

            images = request.FILES.getlist('images')

            print(f"Attributes  {attributes}")

            # Fetch product
            product_instance = Products.objects.filter(pk=product_id).first()
            if not product_instance:
                return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

            # Process attributes for variants
            if product_instance.type == "variant":
                attribute_values = {}
                for attr in attributes:
                    attr_name = attr.get("attribute")
                    attr_values_list = attr.get("values", [])

                    print("Name  :", attr_name)
                    print("Values  :", attr_values_list)

                    if not isinstance(attr_values_list, list):
                        return Response({"message": "Attribute values must be a list"}, status=status.HTTP_400_BAD_REQUEST)

                    attribute_values[attr_name] = attr_values_list

                combinations = list(itertools.product(*attribute_values.values()))

                for combination in combinations:
                    combined_attr = dict(zip(attribute_values.keys(), combination))

                    all_attributes = '-'.join(combination)  

                    # Create the variant name based on attributes
                    name = f"{product_instance.name}-{'-'.join(combination)}"

                    # Save all attribute values in the 'color' column (you can rename this as needed)
                    VariantProducts.objects.create(
                        created_user=User.objects.get(pk=authUser.pk),
                        product=product_instance,
                        name=name,
                        color=all_attributes  # Save all attributes in the 'color' column
                    )

            else:
                for image in images:
                    SingleProducts.objects.create(product=product_instance, created_user=User.objects.get(pk=authUser.pk), image=image)

            return Response({"message": "Product added successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            print("Exception error   :",e)
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VariantProductsByProductView(BaseTokenView):
    def get(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            product = Products.objects.filter(pk=pk).first()
            if not product:
                return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

            # Check product type to determine whether it has variants or is a single product
            if product.type == "variant":
                variant_products = VariantProducts.objects.filter(product=product)
                if not variant_products.exists():
                    return Response({"message": "No variant products found for this product"}, status=status.HTTP_404_NOT_FOUND)
                
                serializer = VariantProductSerializerView(variant_products, many=True)
            else:
                single_product = SingleProducts.objects.filter(product=product)
                if not single_product.exists():
                    return Response({"message": "No single products found for this product"})
                
                serializer = SingleProductsViewSerializer(single_product, many=True)

            return Response({"products": serializer.data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "status": "error",
                "message": "An error occurred",
                "errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        

class VariantProductDetailView(BaseTokenView):
    
    def get_product(self, pk):
        return get_object_or_404(VariantProducts, pk=pk)
        
    def get(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
                
            variant_product = self.get_product(pk)
            if variant_product.is_variant == False:
                sizes = ProductAttributeVariant.objects.filter(variant_product =variant_product )
                for i in sizes:
                    i.delete()
            serializer = VariantProductSerializer(variant_product)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
            
        except VariantProducts.DoesNotExist:
            return Response({"message": "Variant product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            images = request.FILES.getlist('images')
            print(images)
            sizes = request.data.getlist('size',[])
            print(f"size    :{sizes}")
                
            variant_product = self.get_product(pk)
            serializer = VariantProductSerializer(variant_product, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                for size in sizes :
                    ProductAttributeVariant.objects.create(attribute = size ,variant_product = variant_product)
                for image in images:
                    VariantImages.objects.create(variant_product=variant_product ,image=image)
                
                return Response({"message": "Variant product updated successfully", "variant_product": serializer.data}, status=status.HTTP_200_OK)
            
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
        
        except VariantProducts.DoesNotExist:
            return Response({"message": "Variant product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
                
            variant_product = self.get_product(pk)
            variant_product.delete()
            return Response({"message": "Variant product deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        
        except VariantProducts.DoesNotExist:
            return Response({"message": "Variant product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




class VariantProductImageView(APIView):
    def get(self,request,pk):
        try:
            variant_product = VariantProducts.objects.get(pk=pk)
            images = VariantImages.objects.filter(variant_product=variant_product)
            serializer = VariantImageSerilizers(images, many=True)
            return Response({"images": serializer.data}, status=status.HTTP_200_OK)
        except VariantProducts.DoesNotExist:
            return Response({"message": "Variant product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class VariantImageDelete(BaseTokenView):
    def delete(self, request, pk):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            image = get_object_or_404(VariantImages, pk=pk)
            image.delete()
            return Response({"message": "Image deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

        except VariantImages.DoesNotExist:
            return Response({"message": "Image not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class VariantProductsSizeView(APIView):
    def get(self, request,id):
        try:
            products = ProductAttributeVariant.objects.filter(variant_product=id)
            if not  products:
                return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = SizeSerializers(products, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VariantProductsSizeDelete(APIView):
    def delete(self, request, pk):
        try:
            size = get_object_or_404(ProductAttributeVariant, pk=pk)
            size.delete()
            return Response({"message": "Size deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            print(f"Error deleting size: {e}")
            return Response({"message": "An error occurred while deleting the size"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            size = get_object_or_404(ProductAttributeVariant, pk=pk)
            serializer = SizeSerializers(size, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Size updated successfully", "size": serializer.data}, status=status.HTTP_200_OK)
            print(serializer.errors)
            return Response({"message": "Validation error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log the exception details
            print(f"Error updating size: {e}")
            return Response({"message": "An error occurred while updating the size"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    
class CreateOrder(BaseTokenView):
    def post(self, request):
        try :
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
                
            serializer = OrderSerializer(data=request.data)
            if serializer.is_valid():
                order = serializer.save()  # Create order
                
                for item_data in request.data.get('items', []):
                    product_id = item_data.get('product')
                    name = item_data.get('name')
                    quantity = item_data.get('quantity')

                    
                    product_type = Products.objects.filter(pk=product_id).first() 
                    if not product_type:
                        return Response({"status": "error", "message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)


                    if product_type.type == 'single':
                        try:
                            single_product = SingleProducts.objects.get(product=product_type,product__name=name)
                            if single_product.stock < quantity:
                                return Response({"status": "error", "message": "Insufficient stock for single product"}, status=status.HTTP_400_BAD_REQUEST)
                            single_product.stock -= quantity
                            single_product.save()
                        except SingleProducts.DoesNotExist:
                            return Response({"status": "error", "message": "Single product not found"}, status=status.HTTP_404_NOT_FOUND)
                    
                    elif product_type.type == 'variant':
                        try:
                            variant_product = VariantProducts.objects.get(product=product_type,name=name)
                            if variant_product.stock < quantity:
                                return Response({"status": "error", "message": "Insufficient stock for variant product"}, status=status.HTTP_400_BAD_REQUEST)
                            variant_product.stock -= quantity
                            variant_product.save()
                        except VariantProducts.DoesNotExist:
                            return Response({"status": "error", "message": "Variant product not found"}, status=status.HTTP_404_NOT_FOUND)
                    
                    else:
                        return Response({"status": "error", "message": "Invalid product type"}, status=status.HTTP_400_BAD_REQUEST)

                return Response({"status": "success", "message": "Order created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)

            return Response({"status": "error", "message": "Validation failed", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"status": "error", "message": "An unexpected error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class OrderListView(BaseTokenView):
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            orders = Order.objects.all()
            if not orders.exists():
                return Response({"status": "error", "message": "No orders found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = OrderModelSerilizer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Orders not found"}, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError:
            return Response({"status": "error", "message": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class CustomerOrderList(BaseTokenView):
    def get(self, request):
        try:
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response

            orders = Order.objects.filter(manage_staff=authUser)
            if not orders.exists():
                return Response({"status": "error", "message": "No orders found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = OrderModelSerilizer(orders, many=True)
            return Response({"data":serializer.data}, status=status.HTTP_200_OK)

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
        print(serializer.errors)
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
            print(f"Request data: {request.data}")
            authUser, error_response = self.get_user_from_token(request)
            if error_response:
                return error_response
            
            product = get_object_or_404(Products, pk=request.data.get("product"))
            quantity = request.data.get("quantity")
            print(quantity)
            
            if product.type == self.PRODUCT_TYPE_SINGLE:
                return self.add_single_product_to_cart(product, quantity, authUser)
            else:
                if 'variant' not in request.data:
                    return Response({"status": "error", "message": "Variant is required."}, status=status.HTTP_400_BAD_REQUEST)
                
                variant = get_object_or_404(VariantProducts, pk=request.data['variant'])
                
                return self.add_variant_product_to_cart(product, variant, quantity, request, authUser)
        
        except KeyError as e:
            return Response({"status": "error", "message": f"Missing field: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return Response({"status": "error", "message": "An error occurred", "errors": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_single_product_to_cart(self, product, quantity, user):
        """Add a single product to the cart."""
        BeposoftCart.objects.create(product=product, user=user, quantity=quantity)
        return Response({"status": "success", "message": "Product added to cart"}, status=status.HTTP_201_CREATED)

    def add_variant_product_to_cart(self, product, variant, quantity, request, user):
        """Add a variant product to the cart."""
        if variant.is_variant:
            if 'size' not in request.data:
                return Response({"status": "error", "message": "Size is required for this variant product."}, status=status.HTTP_400_BAD_REQUEST)
            
            size = get_object_or_404(ProductAttributeVariant, pk=request.data['size'])
            BeposoftCart.objects.create(product=product, quantity=quantity, variant=variant, user=user, size=size)
        else:
            BeposoftCart.objects.create(product=product, quantity=quantity, variant=variant, user=user)
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
            print(e)
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
    
        
        
