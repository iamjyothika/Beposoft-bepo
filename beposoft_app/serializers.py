from rest_framework import serializers
from .models import *
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    retype_password = serializers.CharField(write_only=True, required=True)
    phone = serializers.CharField(required=True)  # Assuming phone is a required field

    class Meta:
        model = User
        fields = ['name', 'email', 'username', 'password', 'retype_password', 'phone']

    def validate(self, data):
        if data['password'] != data['retype_password']:
            raise serializers.ValidationError("Passwords do not match")
        
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("A user with this email already exists")
        
        if User.objects.filter(phone=data['phone']).exists():
            raise serializers.ValidationError("A user with this phone number already exists")
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('retype_password')

        user = User.objects.create(**validated_data)
        
        return user


    

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = "__all__"


class StaffSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source='department_id.name', read_only=True)

    class Meta:
        model = User
        fields = ['id','eid','name','department','join_date','phone','email','designation']


class CustomerModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customers
        fields = [
            'id', 'gst', 'name', 'manager', 'phone', 'alt_phone', 'email',
            'address', 'zip_code', 'city', 'state', 'comment', 'created_at'
        ]
        
        
        
class CustomerModelSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Customers
        fields = [
            'id', 'gst', 'name', 'manager', 'phone', 'alt_phone', 'email',
            'address', 'zip_code', 'city', 'state', 'comment', 'created_at'
        ]

    def validate(self, data):
        if Customers.objects.filter(gst=data.get('gst')).exists():
            raise serializers.ValidationError({'gst': 'GST number is already registered.'})
        
        if Customers.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({'email': 'Email is already registered.'})
        
        if Customers.objects.filter(phone=data.get('phone')).exists():
            raise serializers.ValidationError({'phone': 'Phone number is already registered.'})

        return data

    # If you want to handle uniqueness checks during updates, override update() method
    def update(self, instance, validated_data):
        gst = validated_data.get('gst', instance.gst)
        email = validated_data.get('email', instance.email)
        phone = validated_data.get('phone', instance.phone)

        # Start a transaction to ensure atomicity
        with transaction.atomic():
            # Check if GST is already registered excluding current instance
            if Customers.objects.filter(gst=gst).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError({'gst': 'GST number is already registered.'})

            # Check if email is already registered excluding current instance
            if Customers.objects.filter(email=email).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError({'email': 'Email is already registered.'})

            # Check if phone is already registered excluding current instance
            if Customers.objects.filter(phone=phone).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError({'phone': 'Phone number is already registered.'})

            # Perform the update operation
            return super().update(instance, validated_data)


class CustomerModelSerializerView(serializers.ModelSerializer):
    state = serializers.CharField(source='state.name', read_only=True)
    manager = serializers.CharField(source ='manager.name',read_only=True)
    class Meta:
        model = Customers
        fields = [
            'id', 'gst', 'name', 'manager', 'phone', 'alt_phone', 'email',
            'address', 'zip_code', 'city', 'state', 'comment', 'created_at'
        ]      
class ProductsSerializer(serializers.ModelSerializer):
    family = serializers.PrimaryKeyRelatedField(many=True, queryset=Family.objects.all())

    class Meta:
        model = Products
        fields = ['id', 'name', 'hsn_code', 'family', 'type', 'unit', 'purchase_rate', 'tax', 'selling_price', 'stock', 'image']



class CustomerSerilizers(serializers.ModelSerializer):
    class Meta :
        model = Customers
        fields = "__all__"



class SingleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SingleProducts
        fields = "__all__"
        
class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = "__all__"
        
        
class SizeSerializers(serializers.ModelSerializer):
    class Meta :
        model = ProductAttributeVariant
        fields = ["id","attribute","stock"]
        
class VariantImageSerilizers(serializers.ModelSerializer):
    class Meta :
        model = VariantImages
        fields  = ["id","image"]
        
class VariantProductSerializerView(serializers.ModelSerializer):
    created_user = serializers.CharField(source="created_user.name") 
    variant_images = VariantImageSerilizers(many=True, read_only=True) 
    sizes = SizeSerializers(many=True, read_only=True)

    class Meta:
        model = VariantProducts
        fields = ['id', 'created_user', 'name', 'stock', 'color', 'is_variant', 'variant_images',"sizes"]
        
    def to_representation(self, instance):
        # Call the parent method to get the default representation
        representation = super().to_representation(instance)

        # If 'is_variant' is False, remove 'sizes' from the serialized output
        if instance.is_variant:
            representation.pop('stock', None)  # Hide stock if is_variant is True
        else:
            representation.pop('sizes', None)  # Hide sizes if is_variant is False
        return representation

class ProductSerializerView(serializers.ModelSerializer):
    single_products = SingleProductSerializer(many=True, read_only=True)
    variant_products = VariantProductSerializerView(many=True, read_only=True)
    

    class Meta:
        model = Products
        fields = [
            "id", "created_user", "name", "hsn_code", "type", "unit", 
            "purchase_rate", "tax", "image", "exclude_price", "selling_price", "stock","single_products","variant_products"
        ]
        
    def to_representation(self, instance):
        # Call the parent method to get the default representation
        representation = super().to_representation(instance)

        # If the product type is 'single', only show 'single_products' and 'stock'
        if instance.type == 'single':
            representation.pop('variant_products', None)  # Hide variant_products
        # If the product type is 'variant', only show 'variant_products'
        elif instance.type == 'variant':
            representation.pop('single_products', None)  # Hide single_products
            representation.pop('stock', None)  # Hide stock if type is variant
        
        return representation

    
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = "__all__"


class DepartmentSerilizers(serializers.ModelSerializer):
    class Meta :
        model = Departments
        fields = "__all__"


    



class StateSerializers(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = "__all__"



class SupervisorSerializerView(serializers.ModelSerializer):
    department = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Supervisor
        fields = ["id","name","department"]
        
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

    def create(self, validated_data):
        created_user = self.context['created_user']
        validated_data['created_user'] = created_user
        return Shipping.objects.create(**validated_data)
    
    
    
class ShippingAddressView(serializers.ModelSerializer):
    state = serializers.CharField(source='state.name', read_only=True)
    class Meta:
        model = Shipping
        fields = ["id","name","email","zipcode","address","phone","country","city","state"]



class VariantProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantProducts
        fields = "__all__"
        

class VariantImageSerilizers(serializers.ModelSerializer):
    class Meta :
        model = VariantImages
        fields  = ["id","image"]
        

class SizeSerializers(serializers.ModelSerializer):
    class Meta :
        model = ProductAttributeVariant
        fields = ["id","attribute","stock"]
        

# class VariantProductSerializerView(serializers.ModelSerializer):
#     created_user = serializers.CharField(source="created_user.name") 
#     variant_images = VariantImageSerilizers(many=True, read_only=True) 
#     sizes = SizeSerializers(many=True, read_only=True)

#     class Meta:
#         model = VariantProducts
#         fields = ['id', 'created_user', 'name', 'stock', 'color', 'is_variant', 'variant_images',"sizes"]

class SingleProductsViewSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product.name")
    class Meta:
        model = SingleProducts 
        fields = ['id','product','image','name']

    

class SingleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SingleProducts
        fields = "__all__"
    


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



class AttributesModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attributes
        exclude = ['created_user']




class ProductAttributeModelSerilizer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = '__all__'










        
