from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('products-by-business/', views.get_products_by_business, name='products_by_business'),
    path('products-by-category-and-business/', views.get_products_by_category_and_business, name='products_by_category_and_business'),
    path('category-list-by-business/', views.get_category_list_by_business, name='category_list_by_business'),
    # Cart endpoints
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/delete/', views.delete_cart_item, name='delete_cart_item'),
    path('cart/list/', views.get_cart_items, name='get_cart_items'),
    # Order endpoints
    path('order/place/', views.place_order, name='place_order'),
    path('order/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    # Payment endpoints
    path('payment/verify/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
    path('payment/status/', views.update_order_payment_status, name='update_order_payment_status'),
    path('payment/fetch-details/', views.fetch_razorpay_payment_details, name='fetch_razorpay_payment_details'),
    path('payment/create-order/', views.create_razorpay_order, name='create_razorpay_order'),
]
