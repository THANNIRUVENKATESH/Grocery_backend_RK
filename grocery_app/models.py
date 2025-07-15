from django.db import models


class BusinessEmployees(models.Model):
    employee_id = models.AutoField(primary_key=True)
    owner = models.ForeignKey('BusinessOwners', models.DO_NOTHING)
    business = models.ForeignKey('Businesses', models.DO_NOTHING)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(unique=True, max_length=20)
    email = models.CharField(unique=True, max_length=100, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    emp_role = models.CharField(max_length=100, blank=True, null=True)
    emp_address = models.TextField(blank=True, null=True)
    emp_city = models.CharField(max_length=45, blank=True, null=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'business_employees'


class BusinessLoginLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    owner = models.ForeignKey('BusinessOwners', models.DO_NOTHING)
    token = models.CharField(max_length=255, blank=True, null=True)
    device_info = models.CharField(max_length=255, blank=True, null=True)
    login_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'business_login_log'


class BusinessOwners(models.Model):
    owner_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=45, blank=True, null=True)
    phone = models.CharField(unique=True, max_length=20)
    email = models.CharField(unique=True, max_length=100, blank=True, null=True)
    password = models.CharField(unique=True, max_length=255, blank=True, null=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    is_superuser = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'business_owners'


class Businesses(models.Model):
    business_id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(BusinessOwners, models.DO_NOTHING)
    business_name = models.CharField(max_length=150)
    business_type = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    business_gst_num = models.CharField(db_column='business_GST_num', max_length=45, blank=True, null=True)  # Field name made lowercase.
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    contact_email = models.CharField(max_length=150, blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    website_url = models.CharField(max_length=255, blank=True, null=True)
    logo_url = models.CharField(max_length=255, blank=True, null=True)
    banner_url = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=9, blank=True, null=True)
    opening_time = models.TimeField(blank=True, null=True)
    closing_time = models.TimeField(blank=True, null=True)
    color_theme = models.CharField(max_length=45, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'businesses'


class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    product = models.ForeignKey('Products', models.DO_NOTHING)
    quantity = models.IntegerField()
    added_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'cart'
        unique_together = ('user', 'product')


class DeliveryDetails(models.Model):
    delivery_id = models.AutoField(primary_key=True)
    order = models.ForeignKey('Orders', models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    business = models.ForeignKey(Businesses, models.DO_NOTHING)
    delivery_address = models.TextField()
    delivery_type = models.CharField(max_length=45,blank=True,null=True)
    delivery_status = models.CharField(max_length=10, blank=True, null=True)
    delivery_person = models.ForeignKey('DeliveryPersons', models.DO_NOTHING, blank=True, null=True)
    estimated_delivery_time = models.DateTimeField(blank=True, null=True)
    actual_delivery_time = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'delivery_details'


class DeliveryPersons(models.Model):
    delivery_person_id = models.AutoField(primary_key=True)
    business = models.ForeignKey(Businesses, models.DO_NOTHING)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(unique=True, max_length=20)
    email = models.CharField(unique=True, max_length=100, blank=True, null=True)
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    id_proof = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'delivery_persons'


class EmployeeLoginLogs(models.Model):
    log_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(BusinessEmployees, models.DO_NOTHING)
    business = models.ForeignKey(Businesses, models.DO_NOTHING, blank=True, null=True)
    login_time = models.DateTimeField(blank=True, null=True)
    logout_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'employee_login_logs'



class Orders(models.Model):
    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    business = models.ForeignKey(Businesses, models.DO_NOTHING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=9, blank=True, null=True)
    order_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders'

class OrderItems(models.Model):
    item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey('Orders', models.DO_NOTHING)
    product = models.ForeignKey('Products', models.DO_NOTHING)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'order_items'


class Payments(models.Model):
    payment_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Orders, models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    business = models.ForeignKey(Businesses, models.DO_NOTHING)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=7, blank=True, null=True)
    payment_method = models.CharField(max_length=4, blank=True, null=True)
    payment_date = models.DateField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'payments'



class TempPayments(models.Model):
    temp_payment_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Orders, models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    business = models.ForeignKey(Businesses, models.DO_NOTHING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=4, blank=True, null=True)
    status = models.CharField(max_length=9, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'temp_payments'


class Products(models.Model):
    product_id = models.AutoField(primary_key=True)
    business = models.ForeignKey(Businesses, models.DO_NOTHING)
    business_type = models.CharField(max_length=100)
    product_name = models.CharField(max_length=150)
    product_image = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(db_column='Category', max_length=45, blank=True, null=True)  # Field name made lowercase.
    food_item_type = models.CharField(max_length=100, blank=True, null=True)
    product_type = models.CharField(max_length=45, blank=True, null=True)
    product_discount = models.CharField(max_length=45, blank=True, null=True)
    is_veg = models.IntegerField(blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    weight = models.CharField(max_length=50, blank=True, null=True)
    mfg_data = models.DateTimeField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    is_organic = models.IntegerField(blank=True, null=True)
    size = models.CharField(max_length=3, blank=True, null=True)
    material = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=6, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    starttime = models.CharField(db_column='startTime', max_length=50, blank=True, null=True)  # Field name made lowercase.
    endtime = models.CharField(db_column='endTime', max_length=45, blank=True, null=True)  # Field name made lowercase.
    stock = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    update_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'products'


class UserLoginLogs(models.Model):
    log_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    token = models.CharField(max_length=255, blank=True, null=True)
    device_info = models.CharField(max_length=255, blank=True, null=True)
    login_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_login_logs'


class Users(models.Model):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=45, blank=True, null=True)
    phone = models.CharField(unique=True, max_length=20)
    email = models.CharField(unique=True, max_length=100, blank=True, null=True)
    otp = models.CharField(max_length=45, blank=True, null=True)
    otp_created_at = models.CharField(max_length=45, blank=True, null=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    is_verified = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
