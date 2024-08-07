from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from .validators import validate_gst
import re
from django.core.exceptions import ValidationError

import random
# Create your models here.


class State(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta :
        db_table = "State"


class Supervisor(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "Supervisor"

    def __str__(self):
        return self.name
    

class Departments(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "Departments"

    def __str__(self):
        return self.name

class Supervisor(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Departments, on_delete=models.CASCADE)

    class Meta:
        db_table = "Supervisor"

    def __str__(self):
        return self.name


class Family(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta :
        db_table = "Family"



class User(models.Model):

    eid = models.CharField(max_length=6, unique=True, editable=False)
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100,unique=True,null=True)
    email = models.EmailField(max_length=100,unique=True)
    phone = models.CharField(max_length=100)
    alternate_number = models.CharField(max_length=10, null=True, blank=True)
    password = models.CharField(max_length=100)
    image = models.ImageField(max_length=100, upload_to="staff_images/", null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    allocated_states = models.ManyToManyField(State)
    gender = models.CharField(max_length=100, null=True, blank=True)
    marital_status = models.CharField(max_length=100, null=True, blank=True)
    driving_license = models.CharField(max_length=100, null=True, blank=True)
    driving_license_exp_date = models.DateField(null=True, blank=True)
    employment_status = models.CharField(max_length=100, null=True, blank=True) #(Full-time  Part-time Contract)
    designation = models.CharField(max_length=100, null=True, blank=True)
    grade = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    city = models.CharField(max_length=100, null=-True,blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    join_date = models.DateField(null=True, blank=True)
    confirmation_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    supervisor_id = models.ForeignKey(Supervisor, on_delete=models.CASCADE, null=True)
    department_id = models.ForeignKey(Departments, on_delete=models.CASCADE, null=True)
    signatur_up = models.ImageField(upload_to="signature/",max_length=100,null=True)
    APPROVAL_CHOICES = [
        ('approved', 'Approved'),
        ('disapproved', 'Disapproved'),
    ]
    approval_status = models.CharField(max_length=100, choices=APPROVAL_CHOICES, default='disapproved', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Handle password hashing
        if self.pk is None or 'password' in kwargs:  
            self.password = make_password(self.password)
        # Handle unique EID
        if not self.eid:
            self.eid = self.generate_unique_eid()
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def generate_unique_eid(self):
        while True:
            eid = str(random.randint(100000, 999999))
            if not User.objects.filter(eid=eid).exists():
                return eid

    class Meta:
        db_table = "User"



class Customers(models.Model):
    gst = models.CharField(
        unique=True,
        max_length=15,
        null=True,
        blank=True,
        validators=[validate_gst],  
    )
    name = models.CharField(max_length=100)
    manager = models.ForeignKey(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=10,unique=True)
    alt_phone = models.CharField(max_length=10, null=True)
    email = models.EmailField(max_length=100,unique=True)
    address = models.CharField(max_length=500,null=True)
    zip_code =models.IntegerField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    comment = models.CharField(max_length=500,null=True)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

    
    class Meta :
        db_table = "Customers"



class Shipping(models.Model):
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=500)
    zipcode = models.IntegerField()
    city = models.CharField(max_length=100)
    state = models.ForeignKey(State,on_delete=models.CASCADE)
    country = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    email = models.CharField(max_length=100)

    class Meta :
        db_table = "Shipping_Address"

    def __str__(self):
        return self.name




class Products(models.Model):
    PRODUCT_TYPES = [
        ('single', 'Single'),
        ('variant', 'Variant'),
    ]
    
    UNIT_TYPES = [
        ('BOX', 'BOX'),
        ('NOS', 'NOS'),
        ('PRS', 'PRS'),
        ('SET', 'SET'),
        ('SET OF 12', 'SET OF 12'),
        ('SET OF 16', 'SET OF 16'),
        ('SET OF 6', 'SET OF 6'),
        ('SET OF 8', 'SET OF 8'),
    ]
    
    name = models.CharField(max_length=500)
    hsn_code = models.CharField(max_length=100)
    family = models.ManyToManyField(Family, related_name='products',null=True)
    type = models.CharField(max_length=100, choices=PRODUCT_TYPES, default='single')
    unit = models.CharField(max_length=100, choices=UNIT_TYPES, default="BOX")
    purchase_rate = models.FloatField()
    tax = models.FloatField() 
    exclude_price = models.FloatField(editable=False)  
    selling_price = models.FloatField(null=True)  

    def calculate_exclude_price(self):
        if self.selling_price is not None:
            self.exclude_price = self.selling_price / (1 + self.tax / 100)
        else:
            self.exclude_price = 0

    def save(self, *args, **kwargs):
        self.calculate_exclude_price()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name




