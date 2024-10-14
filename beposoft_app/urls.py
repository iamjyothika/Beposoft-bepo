from django.urls import path
from .views import *




urlpatterns = [

    path('api/register/', UserRegistrationAPIView.as_view(), name='user-registration'),
    path('api/login/', UserLoginAPIView.as_view(), name='user-login'),


    path('api/profile/',UserProfileData.as_view(),name="UserProfileData"),

    
    path('api/add/customer/', UserCustomerAddingView.as_view(), name='add-customer'),
    path('api/customers/', CustomerView.as_view(), name='customer-list'),
    path('api/customer/update/<int:pk>/', CustomerUpdateView.as_view(), name='customer-update'),


    path('api/add/staff/',CreateUserView.as_view(),name="add-staff"), 
    path('api/staffs/',Users.as_view(),name="staffs"), # completed
    path('api/staff/update/<int:pk>/',UserDataUpdate.as_view(),name="staff-update"),


    path('api/add/family/',FamilyCreatView.as_view(),name="add-family"),  # completed
    path('api/familys/',FamilyAllView.as_view(),name="familys"),  # completed
    path('api/family/update/<int:pk>/',FamilyUpdateView.as_view(),name="family-update"),  # completed


    path('api/add/product/',ProductCreateView.as_view(),name="add-product"), # completed
    path('api/products/',ProductListView.as_view(),name="products"), # completed
    path('api/product/update/<int:pk>/',ProductUpdateView.as_view(),name="product-update"),


    path('api/add/department/',DepartmentCreateView.as_view(),name="add-department"),  # completed
    path('api/departments/',DepartmentListView.as_view(),name="departments"), # completed
    path('api/department/update/<int:pk>/',DepartmentsUpdateView.as_view(),name="department-update"), # completed
    
    
    path ('api/image/delete/<int:pk>/',SingleProductImageView.as_view(),name="image-delete"),  # completed
    path('api/image/add/<int:pk>/',SingleProductImageCreateview.as_view(),name="images-add"),  # completed


    path('api/add/state/',StateCreateView.as_view(),name="add-state"),  # completed
    path('api/states/',StateListView.as_view(),name="states"), # completed
    path('api/state/update/<int:pk>/',StateUpdateView.as_view(),name="state-update"), # completed


    path('api/add/supervisor/',SupervisorCreateView.as_view(),name="add-supervisor"), # completed
    path('api/supervisors/',SuperviserListView.as_view(),name="supervisors"),# completed
    path('api/supervisor/update/<int:pk>/',SupervisorUpdateView.as_view(),name="supervisor-update"),# completed


    path('api/add/cutomer/address/<int:pk>/',ShippingCreateView.as_view(),name="add-customer-address"),# completed
    path('api/update/cutomer/address/<int:pk>/',CustomerShippingAddressUpdate.as_view(),name="address-update"), 


    path('api/add/product/variant/',VariantProductCreate.as_view(),name="add-variant-product"),# completed
    path('api/products/<int:pk>/variants/', VariantProductsByProductView.as_view(), name='variant-products-by-product'), # completed
    path('api/product/<int:pk>/variant/data/', VariantProductDetailView.as_view(), name='variant-product-detail'), # completed


    path('api/add/product/attributes/',ProductAttributeCreate.as_view(),name="add-product-attributes"),
    path('api/product/attributes/',ProductAttributeListView.as_view(),name="product-attributes"),
    path('api/product/attribute/<int:pk>/delete/',ProductAttributeView.as_view(),name="delete-product-attributes"),


    path('api/add/product/attribute/values/',ProductAttributeCreateValue.as_view(),name="add-product-attribute-values"),
    path('api/product/attribute/<int:pk>/values/',ProductAttributeListValue.as_view(),name="product-attribute-values"),
    # path('api/product/attribute/delete/<int:pk>/values/',ProductAttributeDelete.as_view(),name="delete-product-attribute-values"),



    path('api/order/create/', CreateOrder.as_view(), name='create-order'),
    path('api/orders/', OrderListView.as_view(), name='orders'),
    path('api/order/<int:order_id>/items/', CustomerOrderItems.as_view(), name='order-items'),
    path('api/order/status/update/<int:pk>/', CustomerOrderStatusUpdate.as_view(), name='status-update-order'),


    path('api/staff/orders/', CustomerOrderList.as_view(), name='staff-orders'), # staff based orders













]

