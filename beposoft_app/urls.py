from django.urls import path
from .views import *




urlpatterns = [

    path('api/register/', UserRegistrationAPIView.as_view(), name='user-registration'),
    path('api/login/', UserLoginAPIView.as_view(), name='user-login'),


    path('api/profile/',UserProfileData.as_view(),name="UserProfileData"),

    
    path('api/add/customer/', UserCustomerAddingView.as_view(), name='add-customer'),
    path('api/customers/', CustomerView.as_view(), name='customer-list'),
    path('api/customer/update/<int:pk>/', CustomerUpdateView.as_view(), name='customer-update'),
    path('api/customer/delete/<int:pk>/', CustomerDeleteView.as_view(), name='customer-delete'),


    path('api/add/staff/',CreateUserView.as_view(),name="add-staff"),
    path('api/staffs/',Users.as_view(),name="staffs"),
    path('api/staff/update/<int:pk>/',UserDataUpdate.as_view(),name="staff-update"),
    path('api/staff/delete/<int:pk>/',UserDeleteView.as_view(),name="staff-delete"),


    path('api/add/family/',FamilyCreatView.as_view(),name="add-family"),
    path('api/familys/',FamilyAllView.as_view(),name="familys"),
    path('api/family/delete/<int:pk>/',FamilyDataDelete.as_view(),name="family-delete"),
    path('api/family/update/<int:pk>/',FamilyUpdateView.as_view(),name="family-update"),


    path('api/add/product/',ProductCreateView.as_view(),name="add-product"),
    path('api/products/',ProductListView.as_view(),name="products"),
    path('api/product/delete/<int:pk>/',ProductDeleteView.as_view(),name="product-delete"),
    path('api/product/update/<int:pk>/',ProductUpdateView.as_view(),name="product-update"),


    path('api/add/department/',DepartmentCreateView.as_view(),name="add-department"),
    path('api/departments/',DepartmentListView.as_view(),name="departments"),
    path('api/department/delete/<int:pk>/',DepartmentDeleteView.as_view(),name="department-delete"),
    path('api/department/update/<int:pk>/',DepartmentsUpdateView.as_view(),name="department-update"),


    path('api/add/state/',StateCreateView.as_view(),name="add-state"),
    path('api/states/',StateListView.as_view(),name="states"),
    path('api/state/delete/<int:pk>/',StateDeleteView.as_view(),name="state-delete"),
    path('api/state/update/<int:pk>/',StateUpdateView.as_view(),name="state-update"),








]

