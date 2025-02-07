from django.urls import path
from .views import *




urlpatterns = [
    
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),

    path('api/register/', UserRegistrationAPIView.as_view(), name='user-registration'),
    path('api/login/', UserLoginAPIView.as_view(), name='user-login'),


    path('api/profile/',UserProfileData.as_view(),name="UserProfileData"),

    
    path('api/add/customer/', UserCustomerAddingView.as_view(), name='add-customer'),
    path('api/customers/', CustomerView.as_view(), name='customer-list'),
    path('api/staff/customers/', StaffBasedCustomers.as_view(), name='customer-list'),
    path('api/customer/update/<int:pk>/', CustomerUpdateView.as_view(), name='customer-update'),


    path('api/add/staff/',CreateUserView.as_view(),name="add-staff"), 
    path('api/staffs/',Users.as_view(),name="staffs"), # completed  ManagerUnderCustomer
    path('api/staff/orders/',StaffOrders.as_view(),name="staffs"), # completed
    path('api/manager/customers/',ManagerUnderCustomer.as_view(),name="staffs"), # completed
    path('api/staff/update/<int:pk>/',UserDataUpdate.as_view(),name="staff-update"),


    path('api/add/family/',FamilyCreatView.as_view(),name="add-family"),  # completed 
    path('api/familys/',FamilyAllView.as_view(),name="familys"),  # completed
    path('api/family/orders/',FamilyBasedOrderGetView.as_view(),name="familys"),  # completed
    path('api/family/update/<int:pk>/',FamilyUpdateView.as_view(),name="family-update"),  # completed


    path('api/add/product/',ProductCreateView.as_view(),name="add-product"), # completed
    path('api/products/',ProductListView.as_view(),name="products"), # completed
    path('api/all/products/',ListAllProducts.as_view()),
    path('api/product/update/<int:pk>/',ProductUpdateView.as_view(),name="product-update"),


    path('api/add/department/',DepartmentCreateView.as_view(),name="add-department"),  # completed
    path('api/departments/',DepartmentListView.as_view(),name="departments"), # completed
    path('api/department/update/<int:pk>/',DepartmentsUpdateView.as_view(),name="department-update"), # completed
    
    
    path ('api/image/delete/<int:pk>/',SingleProductImageView.as_view(),name="image-delete"),  # completed
    path('api/image/add/<int:pk>/',SingleProductImageCreateView.as_view(),name="images-add"),  # completed


    path('api/add/state/',StateCreateView.as_view(),name="add-state"),  # completed
    path('api/states/',StateListView.as_view(),name="states"), # completed
    path('api/state/update/<int:pk>/',StateUpdateView.as_view(),name="state-update"), # completed


    path('api/add/supervisor/',SupervisorCreateView.as_view(),name="add-supervisor"), # completed
    path('api/supervisors/',SuperviserListView.as_view(),name="supervisors"),# completed
    path('api/supervisor/update/<int:pk>/',SupervisorUpdateView.as_view(),name="supervisor-update"),# completed


    path('api/add/customer/address/<int:pk>/',ShippingCreateView.as_view(),name="add-customer-address"),# completed
    path('api/update/cutomer/address/<int:pk>/',CustomerShippingAddressUpdate.as_view(),name="address-update"), 


    path('api/add/product/variant/',VariantProductCreate.as_view(),name="add-variant-product"),# completed
    path('api/products/<int:pk>/variants/', VariantProductsByProductView.as_view(), name='variant-products-by-product'), # completed
    


    path('api/add/product/attributes/',ProductAttributeCreate.as_view(),name="add-product-attributes"),
    path('api/product/attributes/',ProductAttributeListView.as_view(),name="product-attributes"),
    path('api/product/attribute/<int:pk>/delete/',ProductAttributeView.as_view(),name="delete-product-attributes"),


    path('api/add/product/attribute/values/',ProductAttributeCreateValue.as_view(),name="add-product-attribute-values"),
    path('api/product/attribute/<int:pk>/values/',ProductAttributeListValue.as_view(),name="product-attribute-values"),
    path('api/product/attribute/delete/<int:pk>/values/',ProductAttributeValueDelete.as_view(),name="delete-product-attribute-values"),


    path('api/order/create/', CreateOrder.as_view(), name='create-order'),
    path('api/orders/', OrderListView.as_view(), name='orders'),
    path('api/orders/update/<int:pk>/',OrderUpdateView.as_view()),
    
    path('api/order/<int:order_id>/items/', CustomerOrderItems.as_view(), name='order-items'),
    path('api/order/status/update/<int:pk>/', CustomerOrderStatusUpdate.as_view(), name='status-update-order'),
    path('api/shipping/<int:pk>/order/',ShippingManagementView.as_view(),name = "shipping-management"),
    path('api/add/order/<int:pk>/product/',ExistedOrderAddProducts.as_view()),
    path('api/remove/order/<int:pk>/item/',RemoveExistsOrderItems.as_view()),
    

    

    
   

        
    path('api/staff/customers/',StaffCustomersView.as_view(),name="staff-customers"),
    path('api/cart/product/', Cart.as_view(), name='add-product-cart'),
    path('api/cart/products/',StaffcartStoredProductsView.as_view()),
    path('api/cart/update/<int:pk>/',StaffDeleteCartProduct.as_view()),
    path('api/cart/price/',UpdateCartPricesView.as_view()),
    
    
    
    
    path('api/add/bank/',CreateBankAccountView.as_view()),
    path('api/banks/',BankView.as_view()),
    path('api/bank/view/<int:pk>/',BankAccountView.as_view()),
    
    path('api/company/data/',CreateCompnayDetailsView.as_view()),
    
    
    
    path('api/payment/<int:pk>/reciept/',CreateReceiptAgainstInvoice.as_view()),
    path('api/customer/<int:pk>/ledger/',CustomerOrderLedgerdata.as_view()),
    
    
    path('api/perfoma/invoice/create/',CreatePerfomaInvoice.as_view()),
    path('api/perfoma/invoices/',PerfomaInvoiceListView.as_view()),
    path('api/perfoma/<str:invoice>/invoice/',PerfomaInvoiceDetailView.as_view()),
    
    
    
    path('api/warehouse/data/',WarehouseDataView.as_view()),
    path('api/warehouse/detail/<int:pk>/',WarehouseDetailView.as_view()),
    path('api/warehouse/box/detail/',DailyGoodsView.as_view()),            #deliveryreport
    path('api/warehousedata/<str:date>/',DailyGoodsBydate.as_view()),
    
    
    path('api/grv/data/',GRVaddView.as_view()),
    path('api/getgrv/<int:pk>',GRVGetViewById.as_view()),
    path('api/grv/update/<int:pk>/',GRVUpdateView.as_view()),
    

    path('api/expense/add/',ExpensAddView.as_view()),
    path('api/expense/get/<int:pk>/',ExpenseUpdate.as_view()),


    path('api/salesreport/',SalesReportView.as_view()),
    path('api/invoice/report/<str:date>/',InvoiceReportView.as_view()),

    path('api/bills/<str:date>/<int:pk>/',BillsView.as_view()),
    path('api/credit/sales/',CreditSalesReportView.as_view()),
    
    path('api/credit/bills/<str:date>/',CreditBillsView.as_view()),
    path('api/COD/sales/',CODSalesReportView.as_view()),
    path('api/COD/bills/<str:date>/',CODBillsView.as_view()),

    path('api/stateorder/detail/<int:state_id>/',StateOrderDetailsView.as_view()),

    path('api/deliverylist/report/<str:date>/',DeliveryListView.as_view()),
    path('api/sold/products/',ProductSalesReportView.as_view()),
    
    path('api/product/stock/report/',ProductStockReportView.as_view()),
    path('api/finance-report/',FinancereportAPIView.as_view()),
    
    
    
    
    path('api/parcal/service/',ParcalServiceView.as_view()),
    path('api/parcal/<int:pk>/service/',EditParcalService.as_view()),
    
    path('api/bulk/upload/products/',ProductBulkUploadAPIView.as_view()),
    path('api/bulk/upload/orders/',OrderBulkUploadAPIView.as_view()),
    path('api/bulk/upload/customers/',CustomerUploadView.as_view()),
    path('invoice/<int:pk>/', GenerateInvoice, name='generate_invoice'),


    path('api/warehouse/add/',WarehouseAddView.as_view()),
    
    path('api/warehouse/update/<int:pk>/',WarehouseGetView.as_view()),
    path('api/warehouse/products/<int:warehouse_id>/',ProductByWarehouseView.as_view()),
    path('api/warehouse/orders/<int:warehouse_id>/',WareHouseOrdersView.as_view()),

   
    path('api/attendance/',AttendanceView.as_view()),
    path('api/attendance/update/<int:pk>/', AttendanceUpdateAPIView.as_view(), name='attendance_update'),
    path('api/attendance/report/all/', AllStaffAttendanceReportAPIView.as_view(), name='all_staff_attendance_report'),
    path('api/attendance/absence/<int:staff_id>/', StaffAttendanceAbsenceAPIView.as_view(), name='attendance_absence'),



]





 



   









    




    
    
    
    
    
    
    
    
    


