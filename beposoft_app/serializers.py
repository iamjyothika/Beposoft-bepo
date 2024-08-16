from rest_framework import serializers
from .models import *
from django.contrib.auth.hashers import check_password, make_password

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    retype_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'username', 'password', 'retype_password']

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

class SupervisorViewSerializers(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Supervisor
        fields = ['id', 'name', 'department', 'department_name']


class ShippingSerializers(serializers.ModelSerializer):
    class Meta:
        model = Shipping
        fields = "__all__"



class VariantProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantProducts
        fields = "__all__"


class SingleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SingleProducts
        fields = ['product', 'price', 'stock', 'image']

    def create(self, validated_data):
        created_user = self.context['created_user']
        validated_data['created_user'] = created_user
        return SingleProducts.objects.create(**validated_data)
    


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'name', 'description', 'rate', 'tax', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)  # Nested serializer for order items

    class Meta:
        model = Order
        fields = ['company', 'customer', 'billing_address', 'status', 'total_amount', 'payment_method','manage_staff', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order
    


class OrderModelSerilizer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'



class OrderItemModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'






        
