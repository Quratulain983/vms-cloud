from django.db import models
from django.utils import timezone
import uuid
from cloudinary.models import CloudinaryField


class UserType(models.Model):
    usertype_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'usertype'

    def __str__(self):
        return self.name


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=150, unique=True)
    userpass = models.CharField(max_length=255, default='')
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    client_code = models.CharField(max_length=6, null=True, blank=True)
    image = CloudinaryField('image', blank=True, null=True)
    usertype = models.ForeignKey(UserType, on_delete=models.SET_NULL, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    firebase_uid = models.CharField(max_length=128, null=True, blank=True)


    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    @property
    def is_authenticated(self):
        return True

    class Meta:
        db_table = 'user'







class Project(models.Model):
 
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
 
    project_id = models.AutoField(primary_key=True)
    project_name = models.CharField(max_length=150)
    project_address = models.TextField(blank=True, null=True)
 
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='projects'
    )
 
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_projects'
    )
 
    created_at = models.DateTimeField(auto_now_add=True)
 
    deployed_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='inactive'
    )
 
    class Meta:
        db_table = 'project'
 
    def __str__(self):
        return self.project_name
 

class GatewayType(models.Model):
    gatewaytype_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'gatewaytype'

    def __str__(self):
        return self.name


class GatewaySubType(models.Model):
    gatewaysubtype_id = models.AutoField(primary_key=True)
    gatewaytype = models.ForeignKey(
        GatewayType,
        on_delete=models.CASCADE,
        related_name='subtypes'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'gatewaysubtype'
        unique_together = ('gatewaytype', 'name')

    def __str__(self):
        return f"{self.gatewaytype.name} - {self.name}"


class GatewayDeployStatus(models.Model):
    deploy_status_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'gateway_deploy_status'

    def __str__(self):
        return self.label


class GatewayActiveStatus(models.Model):
    active_status_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'gateway_active_status'

    def __str__(self):
        return self.label


class Gateway(models.Model):
    
    DEPLOYMENT_CHOICES = [
        ('deploy_to_warehouse', 'Deploy to Warehouse'),
        ('assign_to_client', 'Assign to Client'),
        ('assign_to_customer', 'Assign to Customer'),
        ('added_to_warehouse', 'Added to Warehouse'),
        ('allotted_to_client', 'Allotted to Client'),
        ('allotted_to_customer', 'Allotted to Customer'),
        ('deployed_to_customer', 'Deployed to Customer'),
        ('active_to_customer', 'Active to Customer'),
    ]
    ARM_STATUS_CHOICES = [          
        ('arm', 'Arm'),
        ('disarm', 'Disarm'),
    ]
    
    gateway_id = models.AutoField(primary_key=True)
    gateway_name = models.CharField(max_length=150)
    gateway_static_id = models.CharField(max_length=100, blank=True, null=True)
    gateway_password = models.CharField(max_length=255)
    gateway_ssid = models.CharField(max_length=100, blank=True, null=True)
    gateway_mac_address = models.CharField(max_length=100, blank=True, null=True)
    gateway_imei = models.CharField(max_length=100, blank=True, null=True)
    gateway_static_wifi = models.CharField(max_length=100, blank=True, null=True)
    gateway_wifi_ssid = models.CharField(max_length=100, blank=True, null=True)
    gateway_wifi_password = models.CharField(max_length=255, blank=True, null=True)
    gateway_longitude = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    gateway_latitude  = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    arm_status = models.CharField(         
        max_length=10,
        choices=ARM_STATUS_CHOICES,
        default='disarm'
    )
 
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='gateways')
    gatewaytype = models.ForeignKey(GatewayType, on_delete=models.SET_NULL, null=True, related_name='gateways')
    gatewaysubtype = models.ForeignKey(
        GatewaySubType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gateways'
    )
    deploy_status = models.ForeignKey(
        GatewayDeployStatus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gateways'
    )
    active_status = models.ForeignKey(
        GatewayActiveStatus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gateways'
    )
   
    last_seen = models.DateTimeField(null=True, blank=True)
   

    class Meta:
        db_table = 'gateway'

    def __str__(self):
        return self.gateway_name





class GatewayStatus(models.Model):
    
    DEPLOYMENT_CHOICES = [
        ('deploy_to_warehouse', 'Deploy to Warehouse'),
        ('assign_to_client', 'Assign to Client'),
        ('assign_to_customer', 'Assign to Customer'),
        ('added_to_warehouse', 'Added to Warehouse'),
        ('allotted_to_client', 'Allotted to Client'),
        ('allotted_to_customer', 'Allotted to Customer'),
        ('deployed_to_customer', 'Deployed to Customer'),
        ('active_to_customer', 'Active to Customer'),
    ]

    status_id = models.AutoField(primary_key=True)
    
    gateway = models.ForeignKey(
        Gateway,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    
    deployment_status = models.CharField(
        max_length=30,
        choices=DEPLOYMENT_CHOICES,
        default='deploy_to_warehouse'
    )
    
    allotted_to_client = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='client_status_records'
    )
    
    allotted_to_customer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='customer_status_records'
    )
    
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='status_updated_by'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gateway_status'

    def __str__(self):
        return f"{self.gateway.gateway_name} - {self.deployment_status}"
    
    

class GatewayStatusType(models.Model):
    status_id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=255)

    class Meta:
        db_table = 'gateway_status_type'

    def __str__(self):
        return f"{self.status_id} - {self.description}"




class GatewayRelational(models.Model):
    RELATION_TYPE_CHOICES = [
        ('client', 'Client'),
        ('customer', 'Customer'),
    ]

    gatewayrelational_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gateway_relations')
    gateway = models.ForeignKey(Gateway, on_delete=models.CASCADE, related_name='user_relations')
    status = models.ForeignKey(GatewayStatusType, on_delete=models.SET_NULL, null=True, blank=True, related_name='gateway_relations')
    relation_type = models.CharField(
        max_length=20,
        choices=RELATION_TYPE_CHOICES,
        default='customer',
    )
    datetime = models.DateTimeField(null=True, blank=True)
    active_status = models.BooleanField(default=True)
    last_hit_timestamp = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        
        db_table = 'gatewayrelational'
        
class SensorType(models.Model):
    sensortype_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'sensortype'

    def __str__(self):
        return self.name



class Sensor(models.Model):
    sensor_id = models.AutoField(primary_key=True)
    sensor_name = models.CharField(max_length=150)
    sensor_rf_id = models.CharField(max_length=100, blank=True, null=True)
    value = models.JSONField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True, null=True)
    updated_at   = models.DateTimeField(auto_now=True, null=True)

    gateway = models.ForeignKey(
        Gateway,
        on_delete=models.CASCADE,
        related_name='sensors'
    )

    sensortype = models.ForeignKey(
        SensorType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sensors'
    )

    class Meta:
        db_table = 'sensor'
    def __str__(self):
        return self.sensor_name
    





class Camera(models.Model):
    cam_id = models.AutoField(primary_key=True)
    cam_name = models.CharField(max_length=150)
    cam_url = models.URLField(blank=True, null=True)
    cam_rf_id = models.CharField(max_length=100, blank=True, null=True)

    gateway = models.ForeignKey(
        Gateway,
        on_delete=models.CASCADE,
        related_name='cameras'
    )

   
    class Meta:
        db_table = 'camera'

    def __str__(self):
        return self.cam_name
    
class CameraROI(models.Model):
    roi_id = models.AutoField(primary_key=True)
    
    camera = models.ForeignKey(
        Camera,
        on_delete=models.CASCADE,
        related_name='rois'
    )

    roi_name = models.CharField(max_length=150)           
    roi_coordinates = models.CharField(max_length=255)    
    enabled = models.BooleanField(default=True)

    class Meta:
        db_table = 'camera_roi'

    def __str__(self):
        return f"{self.camera.cam_name} - {self.roi_name}"
    
    


class Metadata(models.Model):
    metadata_id = models.AutoField(primary_key=True)
    json_data = models.JSONField(blank=True, null=True)       
    # metadata_json = models.JSONField(blank=True, null=True)   
    timestamp = models.DateTimeField(auto_now_add=True)
    posted_timestamp = models.DateTimeField(null=True, blank=True)
    source_user_id = models.IntegerField(null=True, blank=True)
    device_battery = models.CharField(max_length=50, blank=True, null=True)
    alert = models.BooleanField(default=False)
    warning = models.BooleanField(default=False)
    sensors_alert = models.BooleanField(default=False)
    cam_alert = models.BooleanField(default=False)
    sensors_alert_count = models.IntegerField(default=0)
    cam_alert_count = models.IntegerField(default=0)
    arm = models.BooleanField(default=False)                 
    location = models.JSONField(blank=True, null=True)
    phones = models.JSONField(blank=True, null=True)
    sensors_alert_events = models.JSONField(blank=True, null=True)
    cam_alert_events = models.JSONField(blank=True, null=True)

    gateway = models.ForeignKey(
        Gateway,
        on_delete=models.CASCADE,
        related_name='metadata'
    )

    class Meta:
        db_table = 'metadata'


class SensorHistory(models.Model):
    history_id  = models.AutoField(primary_key=True)
    sensor      = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='history')
    value       = models.JSONField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sensor_history'
        ordering = ['-recorded_at']