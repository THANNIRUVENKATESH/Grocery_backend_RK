from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Users, UserLoginLogs, Products, Cart, Orders, OrderItems, Businesses
import random
import string
from .utils import send_whatsapp_template
from .serializers import UsersSerializer, ProductsSerializer, CartSerializer, OrdersSerializer, PaymentsSerializer, TempPaymentsSerializer
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Func, F, Value, CharField
from django.db import transaction
from collections import defaultdict
from rest_framework.permissions import AllowAny
import traceback
import razorpay
from django.conf import settings
import json

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@api_view(['POST'])
def register(request):
    data = request.data
    first_name = data.get('first_name')
    last_name = data.get('last_name', '')
    email = data.get('email', '')
    phone = data.get('phone')

    if not phone or not first_name:
        resp = {'error': 'Phone and first name are required.'}
        print(resp)
        return Response(resp, status=status.HTTP_400_BAD_REQUEST)

    if Users.objects.filter(phone=phone).exists():
        resp = {'error': 'User already exists.'}
        print(resp)
        return Response(resp, status=status.HTTP_400_BAD_REQUEST)

    otp = ''.join(random.choices(string.digits, k=6))
    now_ist = timezone.now()  # naive datetime, will be IST because USE_TZ=False
    user = Users.objects.create(
        phone=phone,
        first_name=first_name,
        last_name=last_name,
        email=email,
        otp=otp,
        otp_created_at=now_ist,
        is_active=True,
        is_verified=False,
        created_at=now_ist
    )
    send_whatsapp_template(phone, [otp], template_key='register', callback_data='OTP Registration')
    serializer = UsersSerializer(user)
    tokens = get_tokens_for_user(user)
    user.token = tokens['access']
    user.save()
    resp = {'message': 'User registered. OTP sent to WhatsApp.', 'tokens': tokens, 'user': serializer.data}
    print(resp)
    return Response(resp, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def login(request):
    data = request.data
    phone = data.get('phone')
    token = data.get('token')
    if not phone:
        resp = {'error': 'Phone is required.'}
        print(resp)
        return Response(resp, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = Users.objects.get(phone=phone)
    except Users.DoesNotExist:
        resp = {'error': 'User not found.'}
        print(resp)
        return Response(resp, status=status.HTTP_404_NOT_FOUND)
    if token:
        # For backward compatibility, allow login with old token if needed
        if hasattr(user, 'token') and user.token and user.token != token:
            resp = {'error': 'Invalid token.'}
            print(resp)
            return Response(resp, status=status.HTTP_401_UNAUTHORIZED)
        # Token matches, allow login
        serializer = UsersSerializer(user)
        tokens = get_tokens_for_user(user)
        user.token = tokens['access']
        user.save()
        resp = {'message': 'Login successful.', 'tokens': tokens, 'user': serializer.data}
        print(resp)
        return Response(resp, status=status.HTTP_200_OK)
    # If no token, proceed with OTP login
    otp = ''.join(random.choices(string.digits, k=6))
    now_ist = timezone.now()  # naive datetime, will be IST because USE_TZ=False
    user.otp = otp
    user.otp_created_at = now_ist
    user.save()
    send_whatsapp_template(phone, [otp], template_key='login', callback_data='OTP Login')
    resp = {'message': 'OTP sent to WhatsApp.'}
    print(resp)
    return Response(resp, status=status.HTTP_200_OK)

@api_view(['POST'])
def verify_otp(request):
    data = request.data
    phone = data.get('phone')
    otp = data.get('otp')
    device_info = data.get('device_info', '')
    if not phone or not otp:
        resp = {'error': 'Phone and OTP are required.'}
        print(resp)
        return Response(resp, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = Users.objects.get(phone=phone)
    except Users.DoesNotExist:
        resp = {'error': 'User not found.'}
        print(resp)
        return Response(resp, status=status.HTTP_404_NOT_FOUND)
    if user.otp != otp:
        resp = {'error': 'Invalid OTP.'}
        print(resp)
        return Response(resp, status=status.HTTP_400_BAD_REQUEST)
    # Optionally check OTP expiry here
    user.is_verified = True
    user.save()
    now_ist = timezone.now()  # naive datetime, will be IST because USE_TZ=False
    UserLoginLogs.objects.create(user=user, token=None, device_info=device_info, login_time=now_ist)
    serializer = UsersSerializer(user)
    tokens = get_tokens_for_user(user)
    user.token = tokens['access']
    user.save()
    resp = {'message': 'OTP verified.', 'tokens': tokens, 'user': serializer.data}
    print(resp)
    return Response(resp, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_products_by_business(request):
    business_id = request.GET.get('business_id')
    if not business_id:
        return Response({'error': 'business_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
    products = Products.objects.filter(business_id=business_id)
    serializer = ProductsSerializer(products, many=True)
    return Response({'products': serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_products_by_category_and_business(request):
    category = request.GET.get('category')
    category_id = request.GET.get('category_id')
    business_id = request.GET.get('business_id')
    if not business_id:
        return Response({'error': 'business_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
    filters = Q(business_id=business_id)
    products = Products.objects.all()
    if category:
        # Normalize both DB and input: remove spaces and lowercase
        normalized_category = category.replace(' ', '').lower()
        products = products.annotate(
            normalized_category=Func(F('category'), Value(' '), Value(''), function='REPLACE', output_field=CharField())
        ).annotate(
            normalized_category_lower=Func(F('normalized_category'), function='LOWER', output_field=CharField())
        ).filter(normalized_category_lower=normalized_category)
        filters = Q(business_id=business_id)
        if category_id:
            filters &= Q(product_id=category_id)
        products = products.filter(filters)
    else:
        if category_id:
            filters &= Q(product_id=category_id)
        products = Products.objects.filter(filters)
    serializer = ProductsSerializer(products, many=True)
    return Response({'products': serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_category_list_by_business(request):
    business_id = request.GET.get('business_id')
    if not business_id:
        return Response({'error': 'business_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
    categories = Products.objects.filter(business_id=business_id).values_list('category', flat=True).distinct()
    # Remove None or empty categories
    unique_categories = [cat for cat in categories if cat]
    return Response({'categories': unique_categories}, status=status.HTTP_200_OK)

# -------------------- CART APIs --------------------

@api_view(['POST'])
def add_to_cart(request):
    """Add a new item to user's cart or update quantity if same product exists."""
    user_id = request.data.get('user_id')
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))

    if not user_id or not product_id:
        return Response({'error': 'user_id and product_id are required.'}, status=status.HTTP_400_BAD_REQUEST)
    if quantity <= 0:
        return Response({'error': 'quantity must be positive.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Users.objects.get(pk=user_id)
        product = Products.objects.get(pk=product_id)
    except (Users.DoesNotExist, Products.DoesNotExist):
        return Response({'error': 'Invalid user_id or product_id.'}, status=status.HTTP_404_NOT_FOUND)

    # Explicitly check for existing cart item
    existing = Cart.objects.filter(user=user, product=product).first()
    if existing:
        existing.quantity = quantity  # Always set to the new value
        existing.added_at = timezone.now()
        existing.save()
        cart_item = existing
        created = False
    else:
        cart_item = Cart.objects.create(
            user=user, product=product,
            quantity=quantity, added_at=timezone.now()
        )
        created = True

    serializer = CartSerializer(cart_item)
    return Response({'cart_item': serializer.data, 'created': created}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

@api_view(['PUT', 'PATCH'])
def update_cart_item(request):
    """Update the quantity of an existing cart item."""
    cart_id = request.data.get('cart_id')
    quantity = request.data.get('quantity')

    if not cart_id or quantity is None:
        return Response({'error': 'cart_id and quantity are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        quantity = int(quantity)
    except ValueError:
        return Response({'error': 'quantity must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

    if quantity <= 0:
        return Response({'error': 'quantity must be positive.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cart_item = Cart.objects.get(pk=cart_id)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

    cart_item.quantity = quantity
    cart_item.save()

    serializer = CartSerializer(cart_item)
    return Response({'cart_item': serializer.data}, status=status.HTTP_200_OK)

@api_view(['DELETE'])
def delete_cart_item(request):
    """Delete a cart item by its cart_id."""
    cart_id = request.data.get('cart_id') or request.GET.get('cart_id')
    if not cart_id:
        return Response({'error': 'cart_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cart_item = Cart.objects.get(pk=cart_id)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

    cart_item.delete()
    return Response({'message': 'Cart item deleted successfully.'}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_cart_items(request):
    """Retrieve all cart items for a user."""
    user_id = request.GET.get('user_id')
    if not user_id:
        return Response({'error': 'user_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = Users.objects.get(pk=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    cart_items = Cart.objects.filter(user=user).select_related('product')
    serializer = CartSerializer(cart_items, many=True)
    return Response({'cart_items': serializer.data}, status=status.HTTP_200_OK)

# -------------------- ORDER APIs --------------------

@api_view(['POST'])
def place_order(request):
    """Create an order and its order items."""
    data = request.data
    user_id = data.get('user_id')
    business_id = data.get('business_id')
    items = data.get('items', [])

    if not user_id or not business_id:
        return Response({'error': 'user_id and business_id are required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not items:
        return Response({'error': 'items list is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Users.objects.get(pk=user_id)
        business = Businesses.objects.get(pk=business_id)
    except (Users.DoesNotExist, Businesses.DoesNotExist):
        return Response({'error': 'Invalid user_id or business_id.'}, status=status.HTTP_404_NOT_FOUND)

    # Validate products belong to business
    product_ids = [item.get('product_id') for item in items]
    products = Products.objects.filter(product_id__in=product_ids, business=business)
    if products.count() != len(product_ids):
        return Response({'error': 'One or more products are invalid for the given business.'}, status=status.HTTP_400_BAD_REQUEST)

    # Aggregate quantities by product_id
    product_quantities = defaultdict(int)
    for item in items:
        pid = item.get('product_id')
        qty = int(item.get('quantity', 1))
        if qty <= 0:
            return Response({'error': 'quantity must be positive.'}, status=status.HTTP_400_BAD_REQUEST)
        product_quantities[pid] += qty

    with transaction.atomic():
        total_amount = 0
        product_map = {p.product_id: p for p in products}
        for pid, qty in product_quantities.items():
            product = product_map[pid]
            total_amount += product.price * qty

        order = Orders.objects.create(
            user=user,
            business=business,
            total_amount=total_amount,
            status='pending',
            order_time=timezone.now()
        )

        order_items_bulk = []
        for pid, qty in product_quantities.items():
            product = product_map[pid]
            order_items_bulk.append(OrderItems(
                order=order,
                product=product,
                quantity=qty,
                price=product.price
            ))
        OrderItems.objects.bulk_create(order_items_bulk)

    serializer = OrdersSerializer(order)
    return Response({'order': serializer.data}, status=status.HTTP_201_CREATED)

@api_view(['PATCH'])
def update_order_status(request, order_id):
    """Update the status of an order (e.g., from pending to completed)."""
    status_value = request.data.get('status')
    if not status_value:
        return Response({'error': 'status is required.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        order = Orders.objects.get(pk=order_id)
    except Orders.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
    order.status = status_value
    order.save()
    serializer = OrdersSerializer(order)
    return Response({'message': 'Order status updated.', 'order': serializer.data}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_razorpay_payment(request):
    try:
        print('[verify_razorpay_payment] Incoming data:', request.data)
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')
        order_id = request.data.get('order_id')
        user_id = request.data.get('user_id')
        business_id = request.data.get('business_id')
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method', 'razorpay')
        payment_date = timezone.now().date()

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        try:
            client.utility.verify_payment_signature(params_dict)
        except Exception as e:
            print('[verify_razorpay_payment] Signature verification failed:', str(e))
            return Response({'status': 'error', 'message': 'Signature verification failed', 'details': str(e)}, status=400)

        # Store payment in Payments table
        from .models import Payments, Orders, Users, Businesses
        order = Orders.objects.get(pk=order_id)
        user = Users.objects.get(pk=user_id)
        business = Businesses.objects.get(pk=business_id)
        payment = Payments.objects.create(
            order=order,
            user=user,
            business=business,
            payment_reference=razorpay_payment_id,
            transaction_id=razorpay_order_id,
            amount=amount,
            status='success',
            payment_method=payment_method,
            payment_date=payment_date,
            paid_at=timezone.now()
        )

        return Response({'status': 'success', 'message': 'Payment verified and stored', 'payment_id': payment.payment_id}, status=200)
    except Exception as e:
        print('[verify_razorpay_payment] Exception:', str(e))
        print(traceback.format_exc())
        return Response({'status': 'error', 'message': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def update_order_payment_status(request):
    """Update the payment status of an order."""
    try:
        print('[update_order_payment_status] Incoming data:', request.data)
        order_id = request.data.get('order_id')
        payment_status = request.data.get('payment_status')
        if not order_id or not payment_status:
            return Response({'status': 'error', 'message': 'order_id and payment_status are required'}, status=400)
        # Update the order's payment status in the DB
        from .models import Orders
        order = Orders.objects.get(pk=order_id)
        order.status = payment_status
        order.save()
        return Response({'status': 'success', 'message': 'Order payment status updated'}, status=200)
    except Exception as e:
        print('[update_order_payment_status] Exception:', str(e))
        print(traceback.format_exc())
        return Response({'status': 'error', 'message': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def fetch_razorpay_payment_details(request):
    """Fetch payment details from Razorpay using payment_id."""
    try:
        print('[fetch_razorpay_payment_details] Incoming data:', request.data)
        payment_id = request.data.get('payment_id')
        if not payment_id:
            return Response({'status': 'error', 'message': 'payment_id is required'}, status=400)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        payment_details = client.payment.fetch(payment_id)
        return Response({'status': 'success', 'payment_details': payment_details}, status=200)
    except Exception as e:
        print('[fetch_razorpay_payment_details] Exception:', str(e))
        print(traceback.format_exc())
        return Response({'status': 'error', 'message': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_razorpay_order(request):
    """Create a new Razorpay order and return order details."""
    try:
        print('[create_razorpay_order] Incoming data:', request.data)
        amount = request.data.get('amount')
        receipt = request.data.get('receipt', 'grocery_order')
        notes = request.data.get('notes', {})
        if not amount:
            return Response({'status': 'error', 'message': 'amount is required'}, status=400)
        amount_in_paise = int(float(amount) * 100)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': receipt,
            'payment_capture': 1,
            'notes': notes
        })
        return Response({'status': 'success', 'razorpay_order': razorpay_order}, status=200)
    except Exception as e:
        print('[create_razorpay_order] Exception:', str(e))
        print(traceback.format_exc())
        return Response({'status': 'error', 'message': str(e)}, status=500)


