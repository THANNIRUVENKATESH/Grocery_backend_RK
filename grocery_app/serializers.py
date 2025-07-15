from rest_framework import serializers
from .models import Users, UserLoginLogs, Cart, Orders, OrderItems, Products
from django.utils import timezone
import pytz
from datetime import datetime

class UsersSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    otp_created_at = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = '__all__'

    def get_created_at(self, obj):
        if obj.created_at:
            ist = pytz.timezone('Asia/Kolkata')
            dt = obj.created_at
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt)
                except Exception:
                    return dt  # fallback: return as is
            dt = dt.astimezone(ist)
            return dt.strftime('%d-%m-%Y %H:%M:%S IST')
        return None

    def get_otp_created_at(self, obj):
        if obj.otp_created_at:
            ist = pytz.timezone('Asia/Kolkata')
            dt = obj.otp_created_at
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt)
                except Exception:
                    return dt  # fallback: return as is
            dt = dt.astimezone(ist)
            return dt.strftime('%d-%m-%Y %H:%M:%S IST')
        return None

class UserLoginLogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLoginLogs
        fields = '__all__'

class ProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = __import__('grocery_app.models', fromlist=['Products']).Products
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    # Embed product details so frontend has name, price, image etc.
    product = ProductsSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = '__all__' 

# -------------------- ORDER SERIALIZERS --------------------

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductsSerializer(read_only=True)

    class Meta:
        model = OrderItems
        fields = ['item_id', 'product', 'quantity', 'price']

class OrdersSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source='orderitems_set', many=True, read_only=True)

    class Meta:
        model = Orders
        fields = '__all__'

class PaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = __import__('grocery_app.models', fromlist=['Payments']).Payments
        fields = '__all__'

class TempPaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = __import__('grocery_app.models', fromlist=['TempPayments']).TempPayments
        fields = '__all__'