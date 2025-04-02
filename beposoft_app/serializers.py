from rest_framework import serializers 
from .models import *
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Sum
from datetime import datetime
from django.db.models import F, Sum, FloatField
from django.db.models.functions import Cast
from datetime import date
from bepocart.models import *
from bepocart.serializers import *


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
        
        
    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("A user with this email already exists")
        
        if User.objects.filter(phone=data['phone']).exists():
            raise serializers.ValidationError("A user with this phone number already exists")
        
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("A user with this username already exists")
        
        # if User.objects.filter(alternate_number = data['alternate_number']).exists():
        #     raise serializers.ValidationError("A user with this alternate number already exists")
        
        return data



class UserUpdateSerilizers(serializers.ModelSerializer):
    family_name = serializers.CharField(source='family.name', read_only=True)
    supervisor_name=serializers.CharField(source='supervisor_id.name',read_only=True)
    department_name=serializers.CharField(source='department_id.name',read_only=True)
   
  
    
    class Meta:
        model = User
        fields = "__all__"
   
        
        

class StaffSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source='department_id.name', read_only=True)

    class Meta:
        model = User
        fields = ['id','eid','name','department','join_date','phone','email','designation','family','approval_status']


class CustomerModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customers
        fields = [
            'id', 'gst', 'name', 'manager', 'phone', 'alt_phone', 'email',
            'address', 'zip_code', 'city', 'state', 'comment', 'created_at'
        ]
        
        
        
class CustomerModelSerializer(serializers.ModelSerializer):
    gst = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    class Meta:
        model = Customers
        fields = [
            'id', 'gst', 'name', 'manager', 'phone', 'alt_phone', 'email',
            'address', 'zip_code', 'city', 'state', 'comment', 'created_at'
        ]

    def validate(self, data):
        if 'gst' in data and data['gst']:  
            if Customers.objects.filter(gst=data['gst']).exists():
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
    state_id = serializers.IntegerField(source='state.pk', read_only=True)
    manager = serializers.CharField(source ='manager.name',read_only=True)
    family = serializers.CharField(source ='manager.family.pk',read_only=True)
    class Meta:
        model = Customers
        fields = "__all__"

class CustomerModelSerializerLimited(serializers.ModelSerializer):
    family=serializers.CharField(source="manager.family.name")
   
    class Meta:
        model = Customers
        fields = ['id','name', 'email', 'created_at','manager','family','phone']          



class ProductsSerializer(serializers.ModelSerializer):
    family = serializers.PrimaryKeyRelatedField(many=True, queryset=Family.objects.all())
    created_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    warehouses = serializers.PrimaryKeyRelatedField(queryset=WareHouse.objects.all(), required=False)
  


    class Meta:
        model = Products
        fields = "__all__"

class ProductsAddSerializer(serializers.ModelSerializer):
    family = serializers.PrimaryKeyRelatedField(many=True, queryset=Family.objects.all())
    created_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    warehouses = serializers.PrimaryKeyRelatedField(queryset=WareHouse.objects.all(), required=False)
    class Meta:
        model = Products
        exclude = ["exclude_price"]                 




class CustomerSerilizers(serializers.ModelSerializer):
    state = serializers.CharField(source='state.name', read_only=True)
    manager = serializers.CharField(source ='manager.name',read_only=True)
    class Meta :
        model = Customers
        fields = "__all__"

class CustomerOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customers
        fields = ['id','name']



class SingleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SingleProducts
        fields = "__all__"
        
class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = "__all__"
        
        
        

    
    
    
class ProductSingleviewSerializres(serializers.ModelSerializer):
    variantIDs = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Products
        fields = "__all__"

    def get_variantIDs(self, obj):
        """
        If the product is a variant, return all variants for the same groupID,
        ensuring the current product is not included and preventing duplicates.
        """
        if obj.type == 'variant':  # Check if the product is a variant
            # Filter products with the same groupID but exclude the current product
            variants = Products.objects.filter(groupID=obj.groupID).exclude(id=obj.id)
            
            # Track unique attributes to avoid duplicates
            seen_attributes = set()
            variant_list = []

            for variant in variants:
                if variant.image:
                    selected_image = variant.image.url  # Use the updated image directly
                else:
                    # Fetch images for each variant from SingleProducts
                    variant_images = SingleProducts.objects.filter(product=variant.pk)
                    image_urls = [img.image.url for img in variant_images if img.image]

                    # Use first image from SingleProducts if no variant image is set
                    selected_image = image_urls[0] if image_urls else None  


               

                if variant.name not in seen_attributes:
                    seen_attributes.add(variant.name)
                    variant_list.append({
                        "id": variant.pk,
                        "groupID": variant.groupID,
                        "name": variant.name if variant.name else None,  
                        "stock": variant.stock,
                        "locked_stock":variant.locked_stock,
                        
                        "image": selected_image, # Image URL handling
                        "color":variant.color if variant.color else None,
                        "size": variant.size if variant.size else None,
                        "selling_price": variant.selling_price , # Selling price field
                        "created_user":variant.created_user.name,
                        "approval_status":variant.approval_status
                        
                    })

            return variant_list
        return [] 
    
    def get_images(self, obj):
        """Fetch images dynamically using related_name."""
        return [img.image.url for img in obj.images.all()]  
    
    
        

class ProductSerializerView(serializers.ModelSerializer):
    variantIDs = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()  # Fetch images dynamically

    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    

    class Meta:
        model = Products
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)

    # Fetch the main product with the same groupID
        main_product = Products.objects.filter(groupID=instance.groupID).order_by('id').first()


        if instance.type == 'variant' and main_product:
            if not data.get('landing_cost'):
                data['landing_cost'] = main_product.landing_cost
            if not data.get('retail_price'):
                data['retail_price'] = main_product.retail_price
            if not data.get('hsn_code'):
                data['hsn_code'] = main_product.hsn_code 
        data['warehouse_name'] = instance.warehouse.name if instance.warehouse else (
        main_product.warehouse.name if main_product and main_product.warehouse else None
    )          

        return data      

   

    
       
       
    
    
    def get_variantIDs(self, obj):
        

        """
        Fetch variant details for the same groupID, including images.
        """
        main_product = Products.objects.filter(groupID=obj.groupID).order_by('id').first()

        if main_product:  # Ensure correct check for 'variant'
            variants = Products.objects.filter(groupID=obj.groupID)
            variant_list = []
            for variant in variants:
                # If the product itself has an updated image, use it.
                if variant.image:
                    selected_image = variant.image.url  
                else:
                    # Fetch images for each variant from SingleProducts
                    variant_images = SingleProducts.objects.filter(product=variant.pk)
                    image_urls = [img.image.url for img in variant_images if img.image]

                    # Use the first available image from SingleProducts if product.image is missing
                    selected_image = image_urls[0] if image_urls else None 

                hsn_code = variant.hsn_code if variant.hsn_code and variant.hsn_code.strip() else main_product.hsn_code
                
            

            # ✅ Always inherit Warehouse Name from main product if missing
                warehouse_name = variant.warehouse.name if variant.warehouse else (
                    main_product.warehouse.name if main_product.warehouse else None
                )
                

          
                # Fetch images for each variant
                
                variant_list.append({
                    "id": variant.pk,
                    "groupID": variant.groupID,
                    "name": variant.name,
                    "hsn_code":hsn_code,
                    "image":selected_image,  # Use the first image or None
                    "price": variant.selling_price,
                    "color": variant.color if variant.color else None,
                    "size": variant.size if variant.size else None,
                    "stock": variant.stock,
                    "created_user": variant.created_user.name,
                    "warehouse_name": warehouse_name
                    
                   
                })

            return variant_list
        return []
    def get_images(self, obj):
        """Fetch images dynamically using the related name 'images'."""
        return [img.image.url for img in obj.images.all()]  
    

    
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
    # state = serializers.CharField(source='state.name', read_only=True)
    class Meta:
        model = Shipping
        fields = ["id","name","address","zipcode","email","city","phone"]




class SingleProductsViewSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product.name")
    class Meta:
        model = SingleProducts 
        fields = ['id','product','image','name']

    

class SingleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SingleProducts
        fields = "__all__"
        
        
class ExistedOrderAddProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"
    


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'name', 'description', 'rate', 'tax', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    cod_amount = serializers.FloatField(required=False, allow_null=True)
    shipping_mode = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = "__all__"

    # Custom validation to make `cod_amount` not required when `shipping_mode` is provided
    def validate(self, data):
        # If shipping_mode is provided, cod_amount is not required
        if 'shipping_mode' in data and data['shipping_mode'] is not None:
            if 'cod_amount' in data and data['cod_amount'] is None:
                raise serializers.ValidationError({'cod_amount': 'cod_amount cannot be null if shipping_mode is provided.'})
        
        # If cod_amount is provided, ensure shipping_mode can still be optional
        if 'cod_amount' in data and data['cod_amount'] is not None:
            if 'shipping_mode' in data and data['shipping_mode'] is None:
                raise serializers.ValidationError({'shipping_mode': 'shipping_mode cannot be null if cod_amount is provided.'})

        return data
  
     
        
class BankSerializer(serializers.ModelSerializer):
    # created_user = serializers.CharField(source="created_user.name")
    class Meta:
        model = Bank
        fields = "__all__"

class Bankserializers(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ['id', 'name'] 
        

class PaymentRecieptsViewSerializers(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.name")
    bank = serializers.CharField(source="bank.name")
    class Meta :
        model = PaymentReceipt
        fields = '__all__'

class OrderItemModelSerializer(serializers.ModelSerializer):
    image=serializers.ImageField(source="product.image")
    name=serializers.CharField(source="product.name")
    actual_price = serializers.SerializerMethodField()
    exclude_price = serializers.SerializerMethodField()
    price_discount = serializers.SerializerMethodField()
  
    class Meta:
        model = OrderItem
        fields = fields = [
            "id",
            "name",
            "order",
            "product",
            "variant",
            "size",
            "description",
            "rate",
            "tax",
            "discount",
            "quantity",
            "actual_price",
            "exclude_price",
            "price_discount",
            "image"
        ]
    def get_name(self, obj):
        # Check if the product is a single or variant type
        if obj.product.type == "single":
            return obj.product.name
        elif obj.variant:
            return obj.variant.name
        return None
    def get_price_discount(self, obj):
        selling_price = obj.product.selling_price or 0
        discount = obj.discount or 0
        price_discount = max(selling_price - discount, 0)

        return round(price_discount, 2)
    
   
        
    def get_exclude_price(self, obj):
        selling_price = obj.product.selling_price or 0
        discount = obj.discount or 0
        tax = obj.product.tax or 0

        total_price = max(selling_price - discount, 0)
        exclude_price = total_price / (1 + (tax / 100))

        return round(exclude_price, 2)
    
    def get_actual_price(self, obj):
        # directly use exclude_price
        return self.get_exclude_price(obj)

    

    
    
    


class  WarehousedataSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source="order.customer.name")
    phone=serializers.CharField(source="order.customer.phone")
    zip_code=serializers.CharField(source="order.customer.zip_code")
    invoice = serializers.CharField(source="order.invoice")
    family = serializers.CharField(source="order.family.name")
    packed_by=serializers.CharField(source="packed_by.name")
    checked_by = serializers.SerializerMethodField()
    verified_by = serializers.SerializerMethodField()

    def get_checked_by(self, obj):
        return obj.checked_by.name if obj.checked_by is not None else None

    def get_verified_by(self, obj):
        return obj.verified_by.name if obj.verified_by is not None else None


    class Meta:
        model = Warehousedata
        fields = [
            'id', 'box', 'weight', 'length', 'breadth', 'height', 'image',
            'parcel_service', 'tracking_id', 'shipping_charge', 'status',
            'shipped_date', 'order', 'packed_by','verified_by','checked_by', 'customer','phone','zip_code', 'invoice', 'family','actual_weight','parcel_amount','postoffice_date','message_status'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Handle None for parcel_service
        data['parcel_service'] = (
            instance.parcel_service.name if instance.parcel_service else None
        )
        return data
        

 
        
class WarehouseUpdateSerializers(serializers.ModelSerializer):
    class Meta :
        model = Warehousedata
        fields = '__all__'
        
        
# class OrderModelSerilizer(serializers.ModelSerializer):
#     manage_staff = serializers.CharField(source="manage_staff.name")
#     staffID = serializers.CharField(source="manage_staff.pk")
#     pmily = serializers.CharField(source="family.name")
#     bank  = BankSerializer(read_only=True)
#     billing_address = ShippingAddressView(read_only=True)
#     customer = CustomerSerilizers(read_only=True)
#     payment_receipts =  PaymentRecieptsViewSerializers(many=True,read_only=True)
#     customerID = serializers.IntegerField(source="customer.pk")
#     items = OrderItemModelSerializer(read_only = True,  many=True)
#     warehouse=WarehousedataSerializer(many=True,read_only=True)

    
#     class Meta:
#         model = Order
#         fields = "__all__"


class LedgerSerializers(serializers.ModelSerializer):
    recived_payment =  PaymentRecieptsViewSerializers(many=True,read_only=True)
    company = serializers.CharField(source="company.name")
    class Meta :
        model = Order
        fields = ["id","invoice","company","total_amount","order_date","recived_payment"]

        



class AttributesModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attributes
        exclude = ['created_user']

class ProductsListViewSerializers(serializers.ModelSerializer):
    class Meta :
        model = Products
        fields = '__all__'


9
class ProductAttributeModelSerilizer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = '__all__'
        
        
        
class BepocartSerializers(serializers.ModelSerializer):
    class Meta :
        model = BeposoftCart
        fields = "__all__"

        
        
        
class BepocartSerializersView(serializers.ModelSerializer):
    name = serializers.CharField(source="product.name")
    tax = serializers.FloatField(source="product.tax")
    image = serializers.ImageField(source="product.image")
    selling_price = serializers.FloatField(source="product.selling_price")
    retail_price = serializers.FloatField(source="product.retail_price")
    exclude_price = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

  
    class Meta:
        model = BeposoftCart
        fields = [
            "id", "product", "quantity", "discount", "note", "created_at",
            "name", "tax", "exclude_price", "image", "selling_price", "retail_price", "price"
        ]
    def get_price(self, obj):
        # Get the user and check if their designation is 'BDO' or 'BDM'
        user = obj.user
        if user.designation in ['BDO', 'BDM']:
            return obj.product.selling_price  # If designation is BDO or BDM, return the selling price
        return obj.product.retail_price
    
    def get_exclude_price(self, obj):
        selling_price = obj.product.selling_price or 0
        discount = obj.discount or 0
        tax = obj.product.tax or 0

        total_price = max(selling_price - discount, 0)
        exclude_price = total_price / (1 + (tax / 100))

        return round(exclude_price, 2) 
    



class PaymentRecieptSerializers(serializers.ModelSerializer):
    class Meta :
        model = PaymentReceipt
        fields = '__all__'




class PerfomaInvoiceOrderSerializers(serializers.ModelSerializer):
    warehouse_id = serializers.IntegerField(write_only=True) 
    class Meta :
        model = PerfomaInvoiceOrder
        fields = ["manage_staff", "company", "customer", "invoice", "billing_address",
                  "shipping_mode", "code_charge","order_date", "family", "state", "status", "total_amount",
                   "shipping_charge","note", "warehouse_id"]  # Include warehouse_id

    def create(self, validated_data):
        # Extract the warehouse_id from the validated data
        warehouse_id = validated_data.pop("warehouse_id")
        
        # Create the order object first
        order = super().create(validated_data)
        
        # Now link the warehouse to the order using the warehouse_id
        warehouse = WareHouse.objects.get(id=warehouse_id)
        order.warehouses_obj = warehouse
        order.save()

        return order
       
    
    
     

class PerformaOrderListSerilaizer(serializers.ModelSerializer):
    customermame=serializers.CharField(source="customer.name",read_only=True)
    staffname=serializers.CharField(source="manage_staff.name",read_only=True) 
    class Meta:
        model=PerfomaInvoiceOrder
        fields='__all__'       



        
class PerfomaInvoiceProducts(serializers.ModelSerializer):
    images =  serializers.ImageField(source="product.image")
    name = serializers.CharField(source="product.name")
    actual_price = serializers.SerializerMethodField()
    exclude_price = serializers.SerializerMethodField()
    
    class Meta:
        model = PerfomaInvoiceOrderItem
        fields = "__all__"
        
        

    
    def get_actual_price(self, obj):
        # Calculate the actual price based on the product type
        return int(obj.product.selling_price) if obj.product.selling_price is not None else None
    
    def get_exclude_price(self, obj):
        return int(obj.product.exclude_price) if obj.product.exclude_price is not None else None
    

    
        
class PerfomaInvoiceProductsSerializers(serializers.ModelSerializer):
    manage_staff = serializers.CharField(source="manage_staff.id")
    manage_staff_name=serializers.CharField(source="manage_staff.name")
    family = serializers.CharField(source="family.id")
    familyname=serializers.CharField(source="family.name")
 
    billing_address = ShippingAddressView(read_only=True)
    customer = CustomerSerilizers(read_only=True)
    payment_receipts =  PaymentRecieptsViewSerializers(many=True,read_only=True)
    customerID = serializers.IntegerField(source="customer.pk")
    perfoma_items = PerfomaInvoiceProducts(many=True,read_only=True)
    company_name=serializers.CharField(source="company.name")
    warehouse_id = serializers.IntegerField(source="warehouses_obj.id", read_only=True)
    class Meta:
        model = PerfomaInvoiceOrder
        fields = ["id","manage_staff","manage_staff_name","company","company_name","customer",
                  "invoice","billing_address",
                  "shipping_mode","code_charge","order_date","family","familyname",
                  "state","status","total_amount",
                  "payment_receipts",
                  "shipping_charge","customerID","perfoma_items","warehouse_id"]
    def to_representation(self, instance):
        # Add manage_staff_designation to the context of nested serializers
        self.context["manage_staff_designation"] = instance.manage_staff.designation
        return super().to_representation(instance)    

        

class CompanyDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"
        
        


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehousedata
        fields=['box','parcel_service','tracking_id']


class OrderDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)  
    staff_name = serializers.CharField(source='manage_staff.name', read_only=True) 
    family_name=serializers.CharField(source='family.name',read_only=True)
    warehouse=WarehouseSerializer(many=True,read_only=True)
    state = serializers.CharField(source='state.name', read_only=True) 
    recived_payment = PaymentRecieptSerializers(many=True,read_only=True)

    
    class Meta:
        model = Order
        fields = "__all__"

class PaymentReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentReceipt
        fields = ['amount']       


class OrderPaymentSerializer(serializers.ModelSerializer):
    recived_payment = PaymentReceiptSerializer(many=True)
    
    # We will calculate the total paid amount by summing the amount from all related payment receipts
    total_paid = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'invoice', 'order_date', 'payment_status', 'status', 'recived_payment', 'manage_staff', 'customer', 'total_paid']

    def get_total_paid(self, obj):
        # Calculate the total paid amount from all related payment receipts for this order
        total_paid = obj.recived_payment.aggregate(total_paid=Sum('amount'))['total_paid'] or 0
        return total_paid
    
class PaymentReceiptSerializerView(serializers.ModelSerializer):
    bankname=serializers.CharField(source="bank.name")
    invoice=serializers.CharField(source="order.invoice")
    customer=serializers.CharField(source="customer.name")
    created_by=serializers.CharField(source="created_by.name")
    class Meta:
        model = PaymentReceipt
        fields = ["id","payment_receipt","amount","transactionID","received_at","remark","order","customer","bank","invoice","created_by","bankname"]



        
    
class WarehouseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = WareHouse
        fields = "__all__"  


class OrderdetailsSerializer(serializers.ModelSerializer):
    manage_staff = serializers.CharField(source="manage_staff.name", read_only=True)
    staffID = serializers.CharField(source="manage_staff.pk", read_only=True)
    family = serializers.CharField(source="family.name", read_only=True)
    billing_address = ShippingAddressView(read_only=True)
    customer = CustomerOrderSerializer(read_only=True)
    customerID = serializers.IntegerField(source="customer.pk", read_only=True)
    # items = OrderItemModelSerializer(many=True, read_only=True)
    # recived_payment = PaymentRecieptsViewSerializers(many=True, read_only=True)
    state = serializers.CharField(source="state.name", read_only=True)

    class Meta:
        model = Order
        fields = "__all__"





          


class OrderModelSerilizer(serializers.ModelSerializer):
    manage_staff = serializers.CharField(source="manage_staff.name")
    staffID = serializers.CharField(source="manage_staff.pk")
    family = serializers.CharField(source="family.name")
    bank  = BankSerializer(read_only=True)
    billing_address = ShippingAddressView(read_only=True)
    customer = CustomerSerilizers(read_only=True)
    payment_receipts =  PaymentRecieptsViewSerializers(many=True,read_only=True)
    customerID = serializers.IntegerField(source="customer.pk")
    items = OrderItemModelSerializer(read_only = True,  many=True)
    warehouse=WarehousedataSerializer(many=True,read_only=True)
    company = CompanyDetailsSerializer(read_only=True)
    recived_payment = PaymentRecieptsViewSerializers(read_only=True, many=True)
    state = serializers.CharField(source="state.name")

    
    class Meta:
        model = Order
        fields = "__all__"







class WarehouseBoxesDataSerializer(serializers.ModelSerializer):
    class Meta:
        model=Warehousedata
        fields = "__all__"
            
       

# class OrderModelSerilizer(serializers.ModelSerializer):
    # manage_staff = serializers.CharField(source="manage_staff.name")
    # family = serializers.CharField(source="family.name")
    # bank  = BankSerializer(read_only=True)
    # billing_address = ShippingAddressView(read_only=True)
    # customer = CustomerSerilizers(read_only=True)
    # payment_receipts =  PaymentRecieptsViewSerializers(many=True,read_only=True)
    # customerID = serializers.IntegerField(source="customer.pk")
    # warehouse_orders=WarehousedataSerializer(many=True,read_only=True)


    # class Meta:
    #     model = Order
    #     fields = ["id","manage_staff","updated_at","company","customer","invoice","billing_address","shipping_mode","code_charge","order_date","family","state","payment_status","status","total_amount","bank","payment_method","payment_receipts","shipping_charge","customerID","warehouse_orders"]

class GRVSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source="order.customer.name")
    staff=serializers.CharField(source='order.manage_staff.name')
    invoice = serializers.CharField(source = "order.invoice")
    order_date = serializers.CharField(source="order.order_date")
    family=serializers.IntegerField(source="order.family.id")
    class Meta:
        model=GRVModel
        fields=['order','id','product','family','returnreason','price','quantity','remark','note','status','customer','invoice','staff',"order_date",'date','time','updated_at']
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if 'time' in representation and representation['time']:
            try:
                # Convert stored time into 12-hour format for the response
                time_obj = datetime.strptime(representation['time'], '%H:%M:%S')  # Assuming HH:MM:SS storage format
                representation['time'] = time_obj.strftime('%I:%M %p')  # Convert to hh:mm AM/PM
            except ValueError:
                pass  # Leave the time as-is if parsing fails
        return representation  
        # Customize the output format of the time field
           

class GRVModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GRVModel
        fields = ['order', 'product', 'returnreason', 'price', 'quantity', 'remark', 'status', 'date', 'time', 'note', 'updated_at']



class StateBaseOrderSerializers(serializers.ModelSerializer):
    waiting_orders = serializers.SerializerMethodField()
    order_date = serializers.SerializerMethodField()

    class Meta:
        model = State
        fields = ['id', 'name', 'order_date', 'waiting_orders']

    def get_waiting_orders(self, obj):
        waiting_statuses = ['Pending', 'Waiting For Confirmation']
        orders = Order.objects.filter(state=obj, status__in=waiting_statuses)
        return OrderSerializer(orders, many=True).data

    def get_order_date(self, obj):
        # Get the order date from the first waiting order
        first_waiting_order = Order.objects.filter(state=obj, status__in=['Pending', 'Waiting For Confirmation']).first()
        if first_waiting_order:
            return first_waiting_order.order_date
        return None
    

class WareHouseSerializer(serializers.ModelSerializer):
    invoice=serializers.CharField(source="order.invoice")
    customer=serializers.CharField(source="order.customer.name")
    customer_id=serializers.CharField(source="order.customer.id")
    order_date=serializers.DateTimeField(source="order.order_date")
    volume_weight = serializers.SerializerMethodField()

    class Meta:
        model = Warehousedata
        fields= "__all__"

    def get_volume_weight(self, obj):
        try:
            # Ensure length, breadth, and height are converted to float and not None
            length = float(obj.length) if obj.length else 0
            breadth = float(obj.breadth) if obj.breadth else 0
            height = float(obj.height) if obj.height else 0
            return round((length * breadth * height) / 6000, 2)
        except Exception:
            return None
        



class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseModel
        fields = "__all__"

    def validate(self, data):
        """Ensure EMI payments are linked to a loan."""
        purpose = data.get("purpose_of_payment")
        loan = data.get("loan")

        if purpose and hasattr(purpose, 'name') and purpose.name.lower() == 'emi' and not loan:
            raise serializers.ValidationError({"loan": "EMI payments must be associated with a loan."})

        return data
class ExpenseExpectEmiSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ExpenseModel
        fields = ['id','company','payed_by','bank','name','quantity','purpose_of_payment','amount','expense_date','transaction_id','description','added_by']

     # ✅ Always return validated data

class ExpenseSerializerAssest(serializers.ModelSerializer):
    
    class Meta:
        model = ExpenseModel
        fields = ['id','company','category','payed_by','bank','name','quantity','purpose_of_payment','amount','expense_date','transaction_id','description','added_by','asset_types']


        
      
     

    

class ExpenseModelsSerializers(serializers.ModelSerializer):
    company = CompanyDetailsSerializer(read_only=True)
    payed_by = UserUpdateSerilizers(read_only=True)
    bank = Bankserializers(read_only=True)
    categoryname = serializers.SerializerMethodField()
    
    purpose_of_payment=serializers.CharField(source="purpose_of_payment.name") 
    loanname = serializers.SerializerMethodField()
    class Meta:
        model = ExpenseModel
        fields = ['id','company','categoryname','payed_by','bank','purpose_of_payment','amount','expense_date','transaction_id','description','added_by','loan','name','quantity','asset_types',"loanname"]
    
    
    def get_categoryname(self, obj):
        """
        Fetches the category name from the related Category model.
        Returns None if category is not set.
        """
        return obj.category.category_name if obj.category else None

    def get_loanname(self, obj):
        # Check if loanname is not None before accessing emi_name
        return obj.loan.emi_name if obj.loan else None
    
        
        
class ParcalSerializers(serializers.ModelSerializer):
    class Meta:
        model = ParcalService
        fields = "__all__"
        
        
        
class ProductSalesReportSerializer(serializers.ModelSerializer):
    order = serializers.CharField(source="order.invoice")
    product = serializers.CharField(source="product.name")
    total_sold = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    manage_staff = serializers.CharField(source="order.manage_staff.name")

    class Meta:
        model = OrderItem
        fields = ["order", "product", "total_sold", "total_amount", "manage_staff"]

    def get_total_sold(self, obj):
        return obj.quantity  # Assuming `quantity` is the sold quantity

    

    def get_total_amount(self, obj):
        return obj.quantity * obj.rate  # Assuming `rate` is the price per unit



class ProductStockviewSerializres(serializers.ModelSerializer):
    stock = serializers.SerializerMethodField()

    class Meta:
        model = Products
        fields = ["id", "name", "stock", "selling_price","image"]


    def get_stock(self, obj):
        """
        Calculate the total stock for all products with the same groupID,
        including the current product.
        """
        products_in_group = Products.objects.filter(groupID=obj.groupID)
        total_stock = sum(product.stock for product in products_in_group)
        return total_stock

class WarehouseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = WareHouse
        fields = "__all__"  

class OrderRequestSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.name', read_only=True)
    source_warehouse_name = serializers.CharField(source='source_warehouse.name', read_only=True)
    target_warehouse_name = serializers.CharField(source='target_warehouse.name', read_only=True)

    class Meta:
        model = OrderRequest
        fields = ['id', 'product', 'product_name', 'requested_by', 'requested_by_name', 'source_warehouse', 
                  'source_warehouse_name', 'target_warehouse', 'target_warehouse_name', 'quantity', 'status', 
                  'created_at', 'updated_at']
        

class AttendanceSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    staff_designation = serializers.CharField(source='staff.designation', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'staff', 'staff_name', 'staff_designation', 'date', 'attendance_status']        
        
    def validate_attendance_status(self, value):
        """
        Custom validation for attendance status to ensure it's one of the valid options.
        """
        if value not in ['Present', 'Absent', 'Half Day Leave']:
            raise serializers.ValidationError("Invalid status")
        return value

class UpdateCartPricesSerializer(serializers.ModelSerializer):
    selling_price = serializers.FloatField(required=False)
    retail_price = serializers.FloatField(required=False)

    class Meta:
        model = BeposoftCart
        fields = ['id', 'selling_price', 'retail_price']

    def update(self, instance, validated_data):
        # Update only if prices are provided
        if 'selling_price' in validated_data:
            instance.product.selling_price = validated_data['selling_price']
            instance.product.save()

        if 'retail_price' in validated_data:
            instance.product.retail_price = validated_data['retail_price']
            instance.product.save()

        return instance

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choices
        fields = ['id', 'name'] 


    

class CompanyExpenseSeriizers(serializers.ModelSerializer):
    purpose_of_payment = ChoiceSerializer()  # Nested serializer

    class Meta :
        model = ExpenseModel
        fields = ['id','amount','expense_date','purpose_of_payment']


    




class BankbasedReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentReceipt
        fields = ['payment_receipt','amount','received_at']









class FinanaceReceiptSerializer(serializers.ModelSerializer):
    payments=BankbasedReceiptSerializer(read_only=True,many=True)
    banks=CompanyExpenseSeriizers(read_only=True,many=True)
    class Meta:
        model=Bank
        fields = ['id','name','open_balance','payments','banks']


class AttendanceSummarySerializer(serializers.Serializer):
    staff_id = serializers.IntegerField()
    staff_name = serializers.CharField()
    present_count = serializers.IntegerField()
    half_day_leave_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()  


class AttendanceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ["date", "attendance_status"]

class AttendanceAbsenceSerializer(serializers.Serializer):
    staff_id = serializers.IntegerField(source='id')
    staff_name = serializers.CharField(source='name')
    absences = serializers.SerializerMethodField()

    def get_absences(self, obj):
        today = date.today()
        # Filter absences and half-day leaves up to today
        attendance_records = Attendance.objects.filter(
            staff=obj, 
            date__lte=today, 
            attendance_status__in=["Absent", "Half Day Leave"]
        ).order_by("date")

        # Serialize the filtered attendance records
        return AttendanceDetailSerializer(attendance_records, many=True).data          
