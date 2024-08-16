from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(User)
admin.site.register(State)
admin.site.register(Departments)
admin.site.register(Supervisor)
admin.site.register(Customers)
admin.site.register(Products)
admin.site.register(Family)
admin.site.register(Shipping)

admin.site.register(Attributes)
admin.site.register(ProductAttribute)
admin.site.register(VariantProducts)
admin.site.register(Order)
admin.site.register(OrderItem)






