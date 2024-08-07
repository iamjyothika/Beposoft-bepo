from rest_framework import serializers
from .models import *
from django.contrib.auth.hashers import check_password, make_password

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    retype_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'username', 'password', 'retype_password', 'gender']

    def validate(self, data):
        if data['password'] != data['retype_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('retype_password')
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            name=validated_data['name'],
            gender=validated_data.get('gender'),  
            password=validated_data.get('password'),  

        )
        user.save()
        return user
    

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    


class UserSerializer(serializers.ModelSerializer):
    class Meta :
        model = User
        fields = "__all__"


class CustomerModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customers
        fields = [
            'id', 'gst', 'name', 'manager', 'phone', 'alt_phone', 'email',
            'address', 'zip_code', 'city', 'state', 'comment', 'created_at'
        ]
    
    gst = serializers.CharField(
        max_length=15,
        required=False,  
        validators=[validate_gst]
    )
    name = serializers.CharField(max_length=100, required=True)
    manager = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=True)
    phone = serializers.CharField(max_length=10, required=True)
    alt_phone = serializers.CharField(max_length=10, required=False)
    email = serializers.EmailField(max_length=100, required=True)
    address = serializers.CharField(max_length=500, required=True)
    zip_code = serializers.IntegerField(required=True)
    city = serializers.CharField(max_length=100, required=True)
    state = serializers.CharField(max_length=100, required=True)
    comment = serializers.CharField(max_length=500, required=False)
    created_at = serializers.DateField(read_only=True) 

    def validate_gst(value):
        """
        Validate GST number.
        - Should only contain uppercase letters and numbers.
        - Must be exactly 15 characters long.
        """
        # Check if value is None (optional field)
        if value is None:
            return value

        # Check length
        if len(value) != 15:
            raise serializers.ValidationError("GST number must be exactly 15 characters long.")

        # Check if value contains only uppercase letters and numbers
        if not re.match(r'^[A-Z0-9]+$', value):
            raise serializers.ValidationError("GST number must contain only uppercase letters and numbers.")

        return value 
    

class ProductSerilizers(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = "__all__"



class CustomerSerilizers(serializers.ModelSerializer):
    class Meta :
        model = Customers
        fields = "__all__"




class FamilySerilizers(serializers.ModelSerializer):
    class Meta :
        model = Family
        fields ="__all__"


class DepartmentSerilizers(serializers.ModelSerializer):
    class Meta :
        model = Departments
        fields = "__all__"



class StateSerializers(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = "__all__"



class SupervisorSerializers(serializers.ModelSerializer):
    class Meta:
        model = Supervisor
        fields = "__all__"
        
