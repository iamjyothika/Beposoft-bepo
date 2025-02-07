from rest_framework import serializers 
from .models import *
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Sum
from datetime import datetime
from django.db.models import F, Sum, FloatField
from django.db.models.functions import Cast
from datetime import date


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
    manager = serializers.CharField(source ='manager.name',read_only=True)
    family = serializers.CharField(source ='manager.family.pk',read_only=True)
    class Meta:
        model = Customers
        fields = "__all__"  



class ProductsSerializer(serializers.ModelSerializer):
    family = serializers.PrimaryKeyRelatedField(many=True, queryset=Family.objects.all())
    created_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    warehouses = serializers.PrimaryKeyRelatedField(queryset=WareHouse.objects.all(), required=False)
  


    class Meta:
        model = Products
        fields = "__all__"




class CustomerSerilizers(serializers.ModelSerializer):
    state = serializers.CharField(source='state.name', read_only=True)
    manager = serializers.CharField(source ='manager.name',read_only=True)
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
        
        
        

    
    
    
class ProductSingleviewSerializres(serializers.ModelSerializer):
    variantIDs = serializers.SerializerMethodField()
    images = SingleProductSerializer(read_only=True,many=True)

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
                if variant.name not in seen_attributes:
                    seen_attributes.add(variant.name)
                    variant_list.append({
                        "id": variant.pk,
                        "groupID": variant.groupID,
                        "name": variant.name if variant.name else None,  
                        "stock": variant.stock,
                        "image": variant.image.url if variant.image else None,  # Image URL handling
                        "color":variant.color if variant.color else None,
                        "size": variant.size if variant.size else None,
                        "selling_price": variant.selling_price , # Selling price field
                        "created_user":variant.created_user.name
                        
                    })

            return variant_list
        return [] 

class ProductSerializerView(serializers.ModelSerializer):
    variantIDs = serializers.SerializerMethodField()
    images = SingleProductSerializer(read_only=True,many=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    

    class Meta:
        model = Products
        fields = "__all__"
    
    def get_variantIDs(self, obj):
        """
        Fetch variant details for the same groupID, including images.
        """
        if obj.type == 'variant':  # Ensure correct check for 'variant'
            variants = Products.objects.filter(groupID=obj.groupID)
            variant_list = []

            for variant in variants:
                # Fetch images for each variant
                variant_images = SingleProducts.objects.filter(product=variant.pk)
                image_urls = [img.image.url for img in variant_images if img.image]

                variant_list.append({
                    "id": variant.pk,
                    "groupID": variant.groupID,
                    "name": variant.name,
                    "image": image_urls[0] if image_urls else None,  # Use the first image or None
                    "price": variant.selling_price,
                    "color": variant.color if variant.color else None,
                    "size": variant.size if variant.size else None,
                    "stock": variant.stock,
                    "created_user": variant.created_user.name,
                    "warehouse_name": variant.warehouse.name if variant.warehouse else None,
                   
                })

            return variant_list
        return []
    

    
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
    class Meta:
        model = Order
        fields = "__all__"
        
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
    image = serializers.ImageField(source="product.image")
    name = serializers.CharField(source="product.name")
    actual_price = serializers.SerializerMethodField()
    exclude_price = serializers.SerializerMethodField()
    
    
    
    class Meta:
        model = OrderItem
        fields = "__all__"
    def get_actual_price(self, obj):
        # Retrieve the manage_staff_designation from the context
        order = obj.order  # Access the order related to this order item
        manage_staff_designation = order.manage_staff.designation
 
        
        # Print the prices for debugging purposes
      
        # Determine which price to return based on the user's designation
        if manage_staff_designation in ['BDO', 'BDM']:
            return obj.product.selling_price  # Return the selling price if user is BDO or BDM
        else:
          
            return obj.product.retail_price
 
    
    # def get_actual_price(self, obj):
    #     # Calculate the actual price based on the product type
    #     return int(obj.product.selling_price) if obj.product.selling_price is not None else None
    
    def get_exclude_price(self, obj):
        return int(obj.product.exclude_price) if obj.product.exclude_price is not None else None
    


class WarehousedataSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source="order.customer.name")
    invoice = serializers.CharField(source="order.invoice")
    family = serializers.CharField(source="order.family.name")

    class Meta:
        model = Warehousedata
        fields = [
            'id', 'box', 'weight', 'length', 'breadth', 'height', 'image',
            'parcel_service', 'tracking_id', 'shipping_charge', 'status',
            'shipped_date', 'order', 'packed_by', 'customer', 'invoice', 'family','actual_weight','parcel_amount','postoffice_date'
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
        fields = ['parcel_service','tracking_id','shipping_charge','actual_weight','parcel_amount','postoffice_date']
        
        
# class OrderModelSerilizer(serializers.ModelSerializer):
#     manage_staff = serializers.CharField(source="manage_staff.name")
#     staffID = serializers.CharField(source="manage_staff.pk")
#     family = serializers.CharField(source="family.name")
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
    tax = serializers.CharField(source="product.tax")

    exclude_price = serializers.CharField(source="product.exclude_price")
    image = serializers.ImageField(source="product.image")

    price = serializers.SerializerMethodField()
    selling_price = serializers.CharField(source="product.selling_price")
    retail_price = serializers.CharField(source="product.retail_price")
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
    



class PaymentRecieptSerializers(serializers.ModelSerializer):
    class Meta :
        model = PaymentReceipt
        fields = '__all__'




class PerfomaInvoiceOrderSerializers(serializers.ModelSerializer):
    class Meta :
        model = PerfomaInvoiceOrder
        fields = '__all__'
        
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
    manage_staff = serializers.CharField(source="manage_staff.name")
    family = serializers.CharField(source="family.name")
    bank  = BankSerializer(read_only=True)
    billing_address = ShippingAddressView(read_only=True)
    customer = CustomerSerilizers(read_only=True)
    payment_receipts =  PaymentRecieptsViewSerializers(many=True,read_only=True)
    customerID = serializers.IntegerField(source="customer.pk")
    perfoma_items = PerfomaInvoiceProducts(many=True,read_only=True)
    class Meta:
        model = PerfomaInvoiceOrder
        fields = ["id","manage_staff","company","customer",
                  "invoice","billing_address",
                  "shipping_mode","code_charge","order_date","family",
                  "state","payment_status","status","total_amount",
                  "bank","payment_method","payment_receipts",
                  "shipping_charge","customerID","perfoma_items"]
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
    
class WarehouseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = WareHouse
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
    # items = OrderItemModelSerializer(read_only = True,  many=True)
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
    class Meta:
        model=GRVModel
        fields=['order','id','product','returnreason','price','quantity','remark','note','status','customer','invoice','staff',"order_date",'date','time','updated_at']
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
        


class ExpenseModelsSerializers(serializers.ModelSerializer):
    company = CompanyDetailsSerializer(read_only=True)
    payed_by = UserUpdateSerilizers(read_only=True)
    bank = Bankserializers(read_only=True)
    class Meta :
        model = ExpenseModel
        fields = ['id','company','payed_by','bank','purpose_of_payment','amount','expense_date','transaction_id','description','added_by']
        
        
        
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
    

class CompanyExpenseSeriizers(serializers.ModelSerializer):
    class Meta :
        model = ExpenseModel
        fields = ['id','amount','expense_date']


    




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
