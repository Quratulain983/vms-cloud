from django.db import models
from django.utils import timezone
import uuid


# models.py
class User(models.Model):
    ROLES = (
        ('admin', 'Admin'),
        ('user', 'User'),
        ('superadmin', 'superadmin')
    )
    user_id = models.AutoField(primary_key=True)
    firstname = models.CharField(max_length=150)
    lastname = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    contact = models.CharField(max_length=20)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=20, choices=ROLES, default='user')
    image = models.CharField(blank=True, null=True, max_length=500)
    adress = models.CharField(max_length=500, blank=True, null=True, )
    is_online = models.BooleanField(default=False)
    zip_code = models.CharField(max_length=10, blank=True, null=True,)
    unique_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    hardware = models.ManyToManyField('Hardware', blank=True)
    created_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='created_users')

    def __str__(self):
        return self.firstname

class Project(models.Model):
    project_id  = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    # name = models.CharField(max_length=50)
    total_power = models.DecimalField(max_digits=10, decimal_places=2)
    kw = models.DecimalField(max_digits=10, decimal_places=2)
    kva = models.DecimalField(max_digits=10, decimal_places=2)
    power_factor = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.DecimalField(max_digits=10, decimal_places=2)
    current_l1 = models.DecimalField(max_digits=10, decimal_places=2)
    current_l2 = models.DecimalField(max_digits=10, decimal_places=2)
    current_l3 = models.DecimalField(max_digits=10, decimal_places=2)
    volt_l1 = models.DecimalField(max_digits=10, decimal_places=2)
    volt_l2 = models.DecimalField(max_digits=10, decimal_places=2)
    volt_l3 = models.DecimalField(max_digits=10, decimal_places=2)
    power_l1 = models.DecimalField(max_digits=10, decimal_places=2)
    power_l2 = models.DecimalField(max_digits=10, decimal_places=2)
    power_l3 = models.DecimalField(max_digits=10, decimal_places=2)
    time = models.TimeField(auto_now=True)
    last_updated = models.DateTimeField(default=timezone.now) 

    def __str__(self):
        return f"Project {self.project_id} by {self.user_id}"
    
    
class User_Project(models.Model):
    up_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User , on_delete=models.CASCADE)
    hardware_id = models.ForeignKey('Hardware', on_delete=models.CASCADE)

class Hardware(models.Model):
    hardware_id = models.AutoField(primary_key=True)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE, null=True , blank=True)
    name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    is_connected = models.BooleanField(default=False)
    connected_at = models.DateTimeField(auto_now_add=True)
    

class Gateways(models.Model):
    G_id = models.AutoField(primary_key=True)
    gateway_name = models.CharField(max_length=50)
    mac_address = models.CharField(max_length=100, unique=True)
    status = models.BooleanField(default=False)
    deploy_status = models.CharField(
            max_length=20,
            choices=[
                ('warehouse', 'In Warehouse'),
                ('user_aloted', 'Alloted to User'),
                ('deployed', 'Deployed to User'),
            ],
            default='warehouse'
        )
    config = models.BooleanField(default=False)
    user_id = models.ForeignKey(User, null=True , blank=True, on_delete=models.CASCADE)
    project = models.ForeignKey(
        'Project_Manager',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='gateways'  # Make sure this is set if you want to use `project_manager.gateways.all()`
    )
    analyzers_by_port = models.JSONField(default=dict)  # This will store your 'com1', 'com2', 'e1', 'e2' structure
    analyzers = models.ManyToManyField('Analyzer', related_name='gateways')
    created_by_id = models.CharField(max_length=100, unique=False, null=True, blank=True)


    
    def __Str__(self):
        return  self.gateway_name
    
    
class Data(models.Model):
    data_id = models.AutoField(primary_key=True)
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    json_data = models.CharField(max_length=1000)
    
class Project_Manager(models.Model):
    PM_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    longitude = models.DecimalField(max_digits=20, decimal_places=15)
    latitude = models.DecimalField(max_digits=20, decimal_places=15)
    address = models.CharField(max_length=300)
    is_active = models.BooleanField(default=False)


    def __str__(self):
        return self.name

    
    
class Box(models.Model):
    box = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    content = models.JSONField()
    
    def __str__(self):
        return self.name
    
# gateways com1 com2 E1 E2
class Device(models.Model):
    device_type = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    id = models.AutoField(primary_key=True)
    status = models.BooleanField(default=False)
    type = models.CharField(max_length=50)
    value = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(default=timezone.now)

class Gateway(models.Model):
    gateway_id = models.AutoField(primary_key=True)
    gateway_name = models.CharField(max_length=50)
    devices = models.ManyToManyField(Device,related_name='gateways')
    
    def __Str__(self):
        return  self.gateway_name
    
class Com1(models.Model):
    com1_id = models.AutoField(primary_key=True)
    G_id = models.ForeignKey(Gateways , on_delete=models.CASCADE)
    
class Com2(models.Model):
    com2_id = models.AutoField(primary_key=True)
    G_id = models.ForeignKey(Gateways , on_delete=models.CASCADE)
    
class E1(models.Model):
    E1_id = models.AutoField(primary_key=True)
    G_id = models.ForeignKey(Gateways , on_delete=models.CASCADE)
class E2(models.Model):
    E2_id = models.AutoField(primary_key=True)
    G_id = models.ForeignKey(Gateways , on_delete=models.CASCADE)
    
class Analyzer(models.Model):
    analyzer_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    company_name = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    status = models.BooleanField(default=False)
    gateway = models.ForeignKey(Gateways, on_delete=models.CASCADE)
    MOD_id = models.CharField(max_length=100 )
    Date = models.DateField(auto_now_add=True)
    
    # Port information as a choice field (com1, com2, e1, e2)
    PORT_CHOICES = [
        ('com_1', 'Com1'),
        ('com_2', 'Com2'),
        ('e1', 'E1'),
        ('e2', 'E2'),
    ]
    port = models.CharField(max_length=6, choices=PORT_CHOICES)

class MetaData(models.Model):
    MD_id = models.AutoField(primary_key=True)
    date = models.DateTimeField(auto_now_add=True)
    mac_address = models.CharField(max_length=60)
    gateway = models.ForeignKey(Gateways , on_delete=models.CASCADE,related_name='gateways') 
    MOD_id = models.CharField(max_length=60)
    analyzer = models.ForeignKey(Analyzer, on_delete=models.CASCADE, related_name='analyzer')
    gateway = models.ForeignKey(Gateways , on_delete=models.CASCADE,related_name='gateways') 



    created_at = models.DateTimeField(auto_now_add=True)
    for i in range(1, 21):
        exec(f'value{i}_name = models.CharField(max_length=100, blank=True, null=True)')
        exec(f'value{i}_address = models.CharField(max_length=200, blank=True, null=True)')
        exec(f'value{i}_value = models.FloatField(blank=True, null=True)')
        exec(f'value{i}_unit = models.CharField(max_length=200, blank=True, null=True)')
    created_at = models.DateTimeField(auto_now_add=True)
    total_power = models.FloatField(default=0.0)
    setpoint1 = models.FloatField(default=0.0)
    setpoint2 = models.FloatField(default=0.0)
    total_grid = models.FloatField(default=0.0)
    total_Generator = models.FloatField(default=0.0)
    total_solar = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)  # Add timestamp for filtering





class Subscription(models.Model):
    sub_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    warn_days = models.IntegerField(default=30)  # New field
    stop_days = models.IntegerField(default=30)  # New field
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    Active_date = models.DateField(null=True, blank=True)
    deactive = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('Active', 'Active'),
        ('Deactive', 'Deactive')
    ], default='Deactive')

    def __str__(self):
        return f"Subscription {self.sub_id} for {self.user_id}"

class InvoiceTable(models.Model):
    inv_id = models.AutoField(primary_key=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    billing_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue')
    ], default='Pending')


    def save(self, *args, **kwargs):
         
        # Set billing price with discount logic from Subscription
        if self.subscription:
            discount_amount = (self.subscription.price * self.subscription.discount) / 100
            self.billing_price = self.subscription.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.inv_id} for Subscription {self.subscription.sub_id}"


class admincr(models.Model):
    sub_id = models.AutoField(primary_key=True)  # Subscription ID
    cr_id = models.CharField(max_length=20)
    admin_id = models.CharField(max_length=20)
    def __str__(self):
        return f"Subscription {self.sub_id}"


class SensorGateway(models.Model):
    gateway_id = models.CharField(max_length=50, unique=True)
    gateway_mac = models.CharField(max_length=100)
    alert_status = models.CharField(max_length=10, default="0")
    warning_status = models.CharField(max_length=10, default="0")
    arm = models.CharField(max_length=10, default="0")
    address = models.TextField(blank=True, null=True)
    latitude = models.CharField(max_length=50, blank=True, null=True)
    longitude = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.gateway_id} - {self.gateway_mac}"


class Sensor(models.Model):
    gateway = models.ForeignKey(SensorGateway, on_delete=models.CASCADE, related_name="sensors")
    sensor_type = models.CharField(max_length=50)
    sensor_id = models.CharField(max_length=50)
    mac_id = models.CharField(max_length=100)
    sensor_name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, default="0")
    battery = models.CharField(max_length=10, blank=True, null=True)
    rf_status = models.CharField(max_length=20, blank=True, null=True)
    enabled = models.BooleanField(default=True)  # Enable/Disable sensor
    image_url = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        return f"{self.sensor_name} ({self.sensor_type})"

class superadmincr(models.Model):
    sub_id = models.AutoField(primary_key=True)  # Subscription ID
    superadmin_id = models.CharField(max_length=20)
    admin_id = models.CharField(max_length=20)
    def __str__(self):
        return f"Subscription {self.sub_id}"
    

