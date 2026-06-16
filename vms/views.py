from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from datetime import timedelta, timezone as dt_timezone
from .models import (
    Camera,
    CameraROI,
    Gateway,
    GatewayActiveStatus,
    GatewayDeployStatus,
    GatewayRelational,
    GatewayStatus,
    GatewayStatusType,
    GatewaySubType,
    GatewayType,
    Metadata,
    Project,
    Sensor,
    SensorType,
    User,
    UserType,
      SensorHistory, 
)
from django.db import models, transaction
from django.utils.dateparse import parse_datetime
from django.utils import timezone

      

from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from rest_framework.decorators import permission_classes
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q 
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


def attach_sensor_ids(metadata, sensor_map):
    if not metadata:
        return metadata

    for key, value in metadata.items():
        if isinstance(value, list):
            for item in value:
                rf = str(item.get("rf_id"))
                item["sensor_id"] = sensor_map.get(rf)

        elif isinstance(value, dict):
            rf = str(value.get("rf_id"))
            item["sensor_id"] = sensor_map.get(rf)

    return metadata

DEPLOY_STATUS_LABELS = {
    'deploy_to_warehouse': 'Deploy to Warehouse',
    'assign_to_client': 'Assign to Client',
    'assign_to_customer': 'Assign to Customer',
}

ACTIVE_STATUS_LABELS = {
    'connected_no_data_found': 'Gateway connected no data found',
    'connected_wrong_data_found': 'Gateway connected wrong data found',
    'connected_data_found': 'Gateway connected data found',
    'not_connected': 'Gateway not connected',
}


def get_deploy_status(name):
    return GatewayDeployStatus.objects.get_or_create(
        name=name,
        defaults={'label': DEPLOY_STATUS_LABELS.get(name, name.replace('_', ' ').title())}
    )[0]


def get_active_status(name):
    return GatewayActiveStatus.objects.get_or_create(
        name=name,
        defaults={'label': ACTIVE_STATUS_LABELS.get(name, name.replace('_', ' ').title())}
    )[0]


def get_user_type_name(user):
    return (user.usertype.name if user and user.usertype else '').strip().lower()


def is_client(user):
    return get_user_type_name(user) == 'client'


def is_customer(user):
    return get_user_type_name(user) == 'customer'


def is_project_assigned_to_client(project, client):
    if not project or not client:
        return False
    return project.assigned_to_id == client.user_id or project.user_id == client.user_id


def validate_project_client_assignment(project, client):
    if not is_client(client):
        return False, 'Project can only be assigned to a client user.'
    if project and project.assigned_to_id and project.assigned_to_id != client.user_id:
        return False, 'Project is assigned to another client.'
    if is_project_assigned_to_client(project, client):
        return True, None
    return False, 'Project must be assigned to this client before assigning gateways.'


def get_customer_client(customer):
    return customer.parent if customer and is_customer(customer) else None


def get_gateway_client(gateway):
    if not gateway:
        return None
    if gateway.project and gateway.project.assigned_to and is_client(gateway.project.assigned_to):
        return gateway.project.assigned_to

    client_relation = gateway.user_relations.select_related('user', 'user__usertype').filter(
        relation_type='client'
    ).order_by('-assigned_at').first()
    return client_relation.user if client_relation else None


def validate_gateway_client_assignment(gateway, client):
    valid, error = validate_project_client_assignment(gateway.project if gateway else None, client)
    if not valid:
        return False, error.replace('Project', 'Gateway project')
    return True, None


def validate_gateway_customer_assignment(gateway, customer):
    if not is_customer(customer):
        return False, 'Gateway can only be assigned to a customer user at this step.'

    client = get_customer_client(customer)
    if not client or not is_client(client):
        return False, 'Customer is not linked to a valid client.'

    if not is_project_assigned_to_client(gateway.project, client):
        return False, 'Customer client does not own or have this gateway project assigned.'

    gateway_client = get_gateway_client(gateway)
    if gateway_client and gateway_client.user_id != client.user_id:
        return False, 'Gateway is already assigned to a different client.'

    return True, None


def classify_gateway_payload(body):
    metadata = body.get('metadata') if isinstance(body, dict) else None
    if metadata is None:
        return 'connected_no_data_found'
    if not isinstance(metadata, dict):
        return 'connected_wrong_data_found'
    if not metadata:
        return 'connected_no_data_found'
    return 'connected_data_found'


def parse_gateway_timestamp(value):
    if not value:
        return None
    parsed = parse_datetime(str(value))
    if parsed and timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone=dt_timezone.utc)
    return parsed


def extract_gateway_hit_fields(body):
    sensors_alerts = body.get('sensors_alerts') if isinstance(body.get('sensors_alerts'), dict) else {}
    cam_alerts = body.get('cam_alerts') if isinstance(body.get('cam_alerts'), dict) else {}
    sensor_events = sensors_alerts.get('events') if isinstance(sensors_alerts.get('events'), list) else []
    cam_events = cam_alerts.get('events') if isinstance(cam_alerts.get('events'), list) else []
    sensors_alert = bool(sensors_alerts.get('enabled')) and len(sensor_events) > 0
    cam_alert = bool(cam_alerts.get('enabled')) and len(cam_events) > 0

    return {
        'posted_timestamp': parse_gateway_timestamp(body.get('timestamp')),
        'source_user_id': int(body['user_id']) if str(body.get('user_id') or '').isdigit() else None,
        'device_battery': body.get('Device_Battery'),
        'sensors_alert': sensors_alert,
        'cam_alert': cam_alert,
        'sensors_alert_count': len(sensor_events),
        'cam_alert_count': len(cam_events),
        'alert': sensors_alert or cam_alert,
        'warning': False,
        'location': body.get('location') if isinstance(body.get('location'), dict) else None,
        'phones': body.get('phones') if isinstance(body.get('phones'), list) else None,
        'sensors_alert_events': sensor_events,
        'cam_alert_events': cam_events,
    }

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    try:
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return JsonResponse({'error': 'Refresh token required'}, status=400)

        refresh = RefreshToken(refresh_token)

        new_access = refresh.access_token

        return JsonResponse({
            'access': str(new_access),
        }, status=200)

    except TokenError as e:
        return JsonResponse({'error': 'Invalid or expired refresh token'}, status=401)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)





# //creare role
@csrf_exempt
def create_role(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        role = UserType.objects.create(
            name=data.get('name'), 
            description=data.get('description')
        )
        return JsonResponse({'message': 'Role Created', 'id': role.usertype_id})
    
    
@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"DEBUG full data: {data}")        
            print(f"DEBUG usertype_id: {data.get('usertype_id')}")

            role_id = data.get('usertype_id')
            try:
                selected_role = UserType.objects.get(usertype_id=role_id)
            except UserType.DoesNotExist:
                return JsonResponse({'error': 'Role not found'}, status=400)

            if User.objects.filter(username=data.get('username')).exists():
                return JsonResponse({'error': 'Username already exists'}, status=400)

            if User.objects.filter(email=data.get('email')).exists():
                return JsonResponse({'error': 'Email already exists'}, status=400)

            if data.get('phone_number') and User.objects.filter(phone_number=data.get('phone_number')).exists():
                return JsonResponse({'error': 'Phone number already exists'}, status=400)

            parent_user = None
            parent_id = data.get('parent_id')
            if parent_id:
                try:
                    parent_user = User.objects.get(user_id=parent_id)
                except User.DoesNotExist:
                    return JsonResponse({'error': 'Parent user not found'}, status=400)

            client_code = None
            if selected_role.name == 'Client':
                import random
                client_code = f"{random.randint(0, 999999):06d}"

            user = User.objects.create(
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                username=data.get('username'),
                email=data.get('email'),
                phone_number=data.get('phone_number'),
                address=data.get('address'),
                client_code=client_code,
                userpass=data.get('password'),
                icon=data.get('icon'),
                usertype=selected_role,
                parent=parent_user,
            )

            return JsonResponse({
                'message': 'User saved!',
                'user_id': user.user_id,
                'username': user.username,
                'client_code': client_code,
            }, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)







@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            password = data.get('password')

            identifier = data.get('username or email') or data.get('email') or data.get('username')

            if not identifier:
                return JsonResponse({'error': 'username or email required'}, status=400)

            if not password:
                return JsonResponse({'error': 'password required'}, status=400)

            user = User.objects.filter(
                Q(email=identifier) | Q(username=identifier),
                userpass=password
            ).first()

            if user is not None:
                refresh = RefreshToken()
                refresh['user_id'] = user.user_id
                refresh['role'] = user.usertype.name if user.usertype else None

                access = refresh.access_token
                access['user_id'] = user.user_id
                access['role'] = user.usertype.name if user.usertype else None

                return JsonResponse({
                    'refresh': str(refresh),
                    'access': str(access),
                    'user': {
                        'id': user.user_id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.usertype.name if user.usertype else None,
                        'phone_number': user.phone_number,
                        'address': user.address,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                        'image': user.icon,
                        'client_code': user.client_code,
                        'devices': GatewayRelational.objects.filter(user=user).count(),


                    }
                }, status=200)
            else:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)






@csrf_exempt
def update_parent(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            user = User.objects.get(user_id=data.get('user_id'))
            parent = User.objects.get(user_id=data.get('parent_id'))
            user.parent = parent
            user.save()
            return JsonResponse({
                'message': f'{user.username}  parent {parent.username} assigned!'
            }, status=200)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)


@csrf_exempt
def create_project(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Creator (logged in amdin)
            user_id = data.get('user_id')
            if not user_id:
                return JsonResponse({"error": "user_id is required"}, status=400)

            try:
                creator = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                return JsonResponse({"error": "Creator user not found"}, status=404)

            # Assigned client 
            assigned_to_user = None
            assigned_to_id = data.get('assigned_to')
            if assigned_to_id:
                try:
                    assigned_to_user = User.objects.get(user_id=assigned_to_id)
                except User.DoesNotExist:
                    return JsonResponse({"error": "Assigned client not found"}, status=404)

            project = Project.objects.create(
                project_name=data.get('project_name'),
                project_address=data.get('project_address', ''),
                user=creator,
                assigned_to=assigned_to_user,
                deployed_status=data.get('deployed_status', 'inactive'),
            )

            return JsonResponse({
                "message": "Project Created!",
                "id": project.project_id,
                "project_name": project.project_name,
                "deployed_status": project.deployed_status,
                "assigned_to": assigned_to_user.username if assigned_to_user else None,
                "created_at": str(project.created_at),
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)



@csrf_exempt
def update_project(request, project_id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)

            try:
                project = Project.objects.get(project_id=project_id)
            except Project.DoesNotExist:
                return JsonResponse({"error": "Project not found"}, status=404)

            if 'project_name' in data:
                project.project_name = data['project_name']
            if 'project_address' in data:
                project.project_address = data['project_address']
            if 'deployed_status' in data:
                project.deployed_status = data['deployed_status']

            # Assigned to update
            if 'assigned_to' in data:
                assigned_to_id = data['assigned_to']
                if assigned_to_id:
                    try:
                        project.assigned_to = User.objects.get(user_id=assigned_to_id)
                    except User.DoesNotExist:
                        return JsonResponse({"error": "Assigned client not found"}, status=404)
                else:
                    project.assigned_to = None

            project.save()

            return JsonResponse({
                "message": "Project updated!",
                "id": project.project_id,
                "project_name": project.project_name,
                "deployed_status": project.deployed_status,
                "assigned_to": project.assigned_to.username if project.assigned_to else None,
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

def gateway_to_dict(g):
    def safe_decimal(val):
        if val is None or str(val).strip() == '':
            return None
        try:
            return str(val)
        except Exception:
            return None

    latest_status = g.status_history.order_by('-created_at').first()
    latest_metadata = g.metadata.order_by('-timestamp').first()
    latest_client_relation = g.user_relations.select_related('user').filter(
        relation_type='client'
    ).order_by('-assigned_at', '-datetime').first()
    latest_customer_relation = g.user_relations.select_related('user').filter(
        relation_type='customer'
    ).order_by('-assigned_at', '-datetime').first()
    deploy_status = g.deploy_status.name if g.deploy_status else (
        latest_status.deployment_status if latest_status else 'deploy_to_warehouse'
    )
    active_status = g.active_status.name if g.active_status else 'not_connected'

    return {
        'gateway_id': g.gateway_id,
        'gateway_name': g.gateway_name,
        'gateway_static_id': g.gateway_static_id,
        'gateway_mac_address': g.gateway_mac_address,
        'gateway_imei': g.gateway_imei,
        'gateway_ssid': g.gateway_ssid,
        'gateway_longitude': safe_decimal(g.gateway_longitude),
        'gateway_latitude': safe_decimal(g.gateway_latitude),
        'project_id': g.project.project_id if g.project else None,
        'project_name': g.project.project_name if g.project else 'N/A',
        'project_address': g.project.project_address if g.project else 'N/A',
        'gatewaytype_id': g.gatewaytype.gatewaytype_id if g.gatewaytype else None,
        'gateway_type': g.gatewaytype.name if g.gatewaytype else None,
        'gatewaysubtype_id': g.gatewaysubtype.gatewaysubtype_id if g.gatewaysubtype else None,
        'gateway_subtype': g.gatewaysubtype.name if g.gatewaysubtype else None,
        'sensor_count': g.sensors.count(),
        'deployment_status': deploy_status,
        'deploy_status': deploy_status,
        'active_status': active_status,
        'alert': latest_metadata.alert if latest_metadata else False,
        'warning': latest_metadata.warning if latest_metadata else False,
        'sensors_alert': latest_metadata.sensors_alert if latest_metadata else False,
        'cam_alert': latest_metadata.cam_alert if latest_metadata else False,
        'sensors_alert_count': latest_metadata.sensors_alert_count if latest_metadata else 0,
        'cam_alert_count': latest_metadata.cam_alert_count if latest_metadata else 0,
        'last_seen': g.last_seen.isoformat() if g.last_seen else None,
        'allotted_to_client_id': (
            latest_status.allotted_to_client.user_id if latest_status and latest_status.allotted_to_client
            else latest_client_relation.user.user_id if latest_client_relation and latest_client_relation.user else None
        ),
        'allotted_to_client_username': (
            latest_status.allotted_to_client.username if latest_status and latest_status.allotted_to_client
            else latest_client_relation.user.username if latest_client_relation and latest_client_relation.user else None
        ),
        'allotted_to_customer_id': (
            latest_status.allotted_to_customer.user_id if latest_status and latest_status.allotted_to_customer
            else latest_customer_relation.user.user_id if latest_customer_relation and latest_customer_relation.user else None
        ),
        'allotted_to_customer_username': (
            latest_status.allotted_to_customer.username if latest_status and latest_status.allotted_to_customer
            else latest_customer_relation.user.username if latest_customer_relation and latest_customer_relation.user else None
        ),
    } 
    
    
    
    
    
    
    

@csrf_exempt
def create_gateway(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            try:
                proj = Project.objects.get(project_id=data.get('project_id'))
            except Project.DoesNotExist:
                return JsonResponse({"error": "Project not found"}, status=404)

            g_type = None
            if data.get('gatewaytype_id'):
                try:
                    g_type = GatewayType.objects.get(gatewaytype_id=data.get('gatewaytype_id'))
                except GatewayType.DoesNotExist:
                    pass

            g_subtype = None
            if data.get('gatewaysubtype_id'):
                try:
                    g_subtype = GatewaySubType.objects.get(
                        gatewaysubtype_id=data.get('gatewaysubtype_id'),
                        gatewaytype=g_type,
                    )
                except GatewaySubType.DoesNotExist:
                    return JsonResponse({"error": "Gateway subtype not found for selected type"}, status=404)

            allotted_client = None
            if data.get('allotted_to_client'):
                try:
                    allotted_client = User.objects.get(user_id=data['allotted_to_client'])
                except User.DoesNotExist:
                    return JsonResponse({"error": "Client not found"}, status=404)

            allotted_customer = None
            if data.get('allotted_to_customer'):
                try:
                    allotted_customer = User.objects.get(user_id=data['allotted_to_customer'])
                except User.DoesNotExist:
                    return JsonResponse({"error": "Customer not found"}, status=404)

            if allotted_client:
                valid, error = validate_project_client_assignment(proj, allotted_client)
                if not valid:
                    return JsonResponse({"error": error}, status=400)

            if allotted_customer:
                customer_client = get_customer_client(allotted_customer)
                valid, error = validate_project_client_assignment(proj, customer_client)
                if not valid or not customer_client:
                    return JsonResponse({"error": error}, status=400)

            if allotted_customer:
                deploy_status_name = 'assign_to_customer'
            elif allotted_client:
                deploy_status_name = 'assign_to_client'
            else:
                deploy_status_name = data.get('deployment_status', 'deploy_to_warehouse')

            gateway = Gateway.objects.create(
                gateway_name=data.get('gateway_name'),
                gateway_static_id=data.get('gateway_static_id'),
                gateway_password=data.get('gateway_password', 'default_pass'),
                gateway_ssid=data.get('gateway_ssid'),
                gateway_mac_address=data.get('gateway_mac_address'),
                gateway_imei=data.get('gateway_imei'),
                gateway_static_wifi=data.get('gateway_static_wifi'),
                gateway_wifi_ssid=data.get('gateway_wifi_ssid'),
                gateway_wifi_password=data.get('gateway_wifi_password'),
                gateway_longitude=data.get('gateway_longitude'),
                gateway_latitude=data.get('gateway_latitude'),
                project=proj,
                gatewaytype=g_type,
                gatewaysubtype=g_subtype,
                deploy_status=get_deploy_status(deploy_status_name),
                active_status=get_active_status('not_connected'),
               
            )

            GatewayStatus.objects.create(
                gateway=gateway,
                deployment_status=deploy_status_name,
                allotted_to_client=allotted_client,
                allotted_to_customer=allotted_customer,
            )

            return JsonResponse({
                "message": "Gateway created!",
                "gateway_id": gateway.gateway_id
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400) 
 
 
 
 
 
 
 
       
@csrf_exempt
def create_gateway_type(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            g_type = GatewayType.objects.create(
                name=data.get('name'),
                description=data.get('description')
            )
            return JsonResponse({
                "message": "Gateway Type created!",
                "gatewaytype_id": g_type.gatewaytype_id
            }, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        
        
@csrf_exempt
def assign_gateway_to_user(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data        = json.loads(request.body)
        user_id     = data.get('user_id')
        gateway_id  = data.get('gateway_id')

        if not user_id or not gateway_id:
            return JsonResponse({"error": "user_id and gateway_id are required"}, status=400)

        user_obj    = User.objects.select_related('usertype').get(user_id=user_id)
        gateway_obj = Gateway.objects.get(gateway_id=gateway_id)

        usertype_name = user_obj.usertype.name.lower() if user_obj.usertype else ''

        if usertype_name == 'client':
            valid, error = validate_gateway_client_assignment(gateway_obj, user_obj)
            if not valid:
                return JsonResponse({"error": error}, status=400)
            deployment_status = 'assign_to_client'
            status_kwargs = {'allotted_to_client': user_obj}
            relation_type = 'client'
        elif usertype_name == 'customer':
            valid, error = validate_gateway_customer_assignment(gateway_obj, user_obj)
            if not valid:
                return JsonResponse({"error": error}, status=400)
            deployment_status = 'assign_to_customer'
            status_kwargs = {'allotted_to_customer': user_obj}
            relation_type = 'customer'
        else:
            deployment_status = 'deploy_to_warehouse'
            status_kwargs = {}
            relation_type = 'customer'

        gateway_obj.deploy_status = get_deploy_status(deployment_status)
        gateway_obj.save(update_fields=['deploy_status'])

        relation, created = GatewayRelational.objects.get_or_create(
            user=user_obj,
            gateway=gateway_obj,
            defaults={
                'relation_type': relation_type,
                'datetime': timezone.now(),
                'last_hit_timestamp': timezone.now(),
                'active_status': True,
            }
        )
        if not created:
            relation.relation_type = relation_type
            relation.datetime = timezone.now()
            relation.active_status = True
            relation.save(update_fields=['relation_type', 'datetime', 'active_status'])

        GatewayStatus.objects.create(
            gateway=gateway_obj,
            deployment_status=deployment_status,
            updated_by=user_obj,
            **status_kwargs,
        )

        return JsonResponse({
            "message":           f"Gateway '{gateway_obj.gateway_name}' assigned to {user_obj.username}",
            "relation_id":       relation.gatewayrelational_id,
            "deployment_status": deployment_status,
            "already_existed":   not created,
        }, status=201)

    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Gateway.DoesNotExist:
        return JsonResponse({"error": "Gateway not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)



@csrf_exempt
def create_sensor(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            gateway_obj = Gateway.objects.get(gateway_id=data.get('gateway_id'))
            
            sensortype_obj = None
            if data.get('sensortype_id'):
                sensortype_obj = SensorType.objects.get(sensortype_id=data.get('sensortype_id'))
            
            sensor = Sensor.objects.create(
                sensor_name=data.get('sensor_name'),
                sensor_rf_id=data.get('sensor_rf_id'),
                gateway=gateway_obj,
                sensortype=sensortype_obj  
            )
            return JsonResponse({"message": "Sensor added!", "id": sensor.sensor_id}, status=201)
        except SensorType.DoesNotExist:
            return JsonResponse({"error": "Invalid sensortype_id"}, status=400)
        except Gateway.DoesNotExist:
            return JsonResponse({"error": "Invalid gateway_id"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def create_camera(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            gateway_obj = Gateway.objects.get(gateway_id=data.get('gateway_id'))
            
            camera = Camera.objects.create(
                cam_name=data.get('cam_name'),
                cam_url=data.get('cam_url'),
                cam_rf_id=data.get('cam_rf_id'),
                gateway=gateway_obj
            )
            return JsonResponse({"message": "Camera added!", "id": camera.cam_id}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


####################################################
#  ADMIN VIEWS

# 1. Admin all Clients
@csrf_exempt
def admin_clients(request, admin_id):
    if request.method == 'GET':
        clients = User.objects.filter(
            parent_id=admin_id,
            usertype__name='Client'
        )
        data = [{
            'user_id': c.user_id,
            'username': c.username,
            'email': c.email,
            'project_count': Project.objects.filter(
                models.Q(user_id=c.user_id) | models.Q(assigned_to_id=c.user_id)
            ).count(),
        } for c in clients]
        return JsonResponse({'clients': data}, status=200)

# 2.specific  Client Customers
@csrf_exempt
def admin_client_customers(request, client_id):
    if request.method == 'GET':
        customers = User.objects.filter(
            parent_id=client_id,
            usertype__name='Customer'
        ).select_related('parent')
        data = []
        for cu in customers:
            gateways = GatewayRelational.objects.filter(
                user=cu
            ).select_related(
                'gateway', 'gateway__project', 'gateway__gatewaytype',
                'gateway__gatewaysubtype', 'gateway__deploy_status',
                'gateway__active_status'
            )
            data.append({
                'user_id': cu.user_id,
                'username': cu.username,
                'email': cu.email,
                'client_name': cu.parent.username if cu.parent else 'N/A',
                'gateway_count': gateways.count(),
                'gateways': [r.gateway.gateway_name for r in gateways],
                'projects': [
                    {
                        'gateway_name': r.gateway.gateway_name,
                        'project_name': r.gateway.project.project_name,
                        'project_id': r.gateway.project.project_id,
                    }
                    for r in gateways
                    if r.gateway.project
                ],
            })
        return JsonResponse({'customers': data}, status=200)

# 3. Admins Projects (through clients)
@csrf_exempt
def admin_projects(request, admin_id):
    if request.method == 'GET':
        projects = Project.objects.filter(
            models.Q(user_id=admin_id) | 
            models.Q(user__parent_id=admin_id, user__usertype__name='Client') 
        ).select_related('user', 'assigned_to')

        data = [{
            'project_id': p.project_id,
            'project_name': p.project_name,
            'project_address': p.project_address,
            'client_name': p.user.username if p.user else 'N/A',
            'assigned_to_username': p.assigned_to.username if p.assigned_to else 'N/A',
            'assigned_to_id': p.assigned_to.user_id if p.assigned_to else None,
            'gateway_count': p.gateways.count(),
            'created_at': str(p.created_at) if p.created_at else None,
            'deployed_status': p.deployed_status,
        } for p in projects]
        return JsonResponse({'projects': data}, status=200)

# 4. Project  Gateways
@csrf_exempt
def admin_project_gateways(request, project_id):
    if request.method == 'GET':
        gateways = Gateway.objects.filter(
            project_id=project_id
        ).select_related(
            'project', 'project__user',
            'gatewaytype', 'gatewaysubtype', 'deploy_status', 'active_status'
        ).prefetch_related('status_history')
        return JsonResponse({'gateways': [gateway_to_dict(g) for g in gateways]}, status=200)
    
    
    
# 5. Admins all Clients Customers
@csrf_exempt
def all_admin_customers(request, admin_id):
    if request.method == 'GET':
        try:
            client_ids = User.objects.filter(
                parent_id=admin_id,
                usertype__name='Client'
               
            ).values_list('user_id', flat=True)

            customers = User.objects.filter(
                parent_id__in=list(client_ids),
                usertype__name='Customer'
            ).select_related('parent')

            data = []
            for cu in customers:
                gateways = GatewayRelational.objects.filter(
                    user=cu
                ).select_related('gateway', 'gateway__project')
                data.append({
                    'user_id': cu.user_id,
                    'username': cu.username,
                    'email': cu.email,
                    'client_name': cu.parent.username if cu.parent else "N/A",
                    'gateway_count': gateways.count(),
                    'gateways': [r.gateway.gateway_name for r in gateways],
                    'projects': [
                        {
                            'gateway_name': r.gateway.gateway_name,
                            'project_name': r.gateway.project.project_name,
                            'project_id': r.gateway.project.project_id,
                        }
                        for r in gateways
                        if r.gateway.project
                    ],
                })
            return JsonResponse({'customers': data}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)      
                  
# 6. gateways under admin
@csrf_exempt
def all_admin_gateways(request, admin_id):
    if request.method == 'GET':
        try:
            gateways = Gateway.objects.filter(
                models.Q(project__user_id=admin_id) |
                models.Q(project__user__parent_id=admin_id)
            ).select_related(
              'project', 'project__user',
               'gatewaytype', 'gatewaysubtype', 'deploy_status', 'active_status'
            ).prefetch_related('status_history')

            data = []
            for g in gateways:
                try:
                    data.append(gateway_to_dict(g))
                except Exception as e:
                    print(f"FAILED gateway_id={g.gateway_id} | long={g.gateway_longitude!r} | lat={g.gateway_latitude!r} | ERROR={e}")

            return JsonResponse({'gateways': data}, status=200)

        except Exception as e:
            import traceback
            print("FULL TRACEBACK:", traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)



@csrf_exempt  
def admin_details_view(request):
    if request.method == 'GET':
        admins = User.objects.filter(usertype__name='Admin')
        data = []
        for a in admins:
            clients = User.objects.filter(parent=a, usertype__name='Client')
            total_customers = User.objects.filter(
                parent__in=clients, 
                usertype__name='Customer'
            ).count()
            total_projects = Project.objects.filter(
                Q(user=a) |
                Q(assigned_to__in=clients) |
                Q(user__in=clients)
            ).distinct().count()  
            
            data.append({
                'id': a.user_id,
                'username': a.username,
                'email': a.email,
                'icon': a.icon or '',          
                'usertype_id': a.usertype.usertype_id if a.usertype else '',  
                'parent_id': a.parent.user_id if a.parent else '',           
                'total_clients': clients.count(),
                'total_customers': total_customers,
                'total_projects': total_projects,
})
        return JsonResponse(data, safe=False)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
 
 
 
 
 
 
 
    
#all list of  all clients    
@csrf_exempt
def get_all_clients_for_superadmin(request):
    if request.method == 'GET':
        clients = User.objects.filter(usertype__name='Client')
        data = [{
            'user_id': c.user_id,
            'username': c.username,
            'email': c.email,
            'project_count': Project.objects.filter(
                models.Q(user_id=c.user_id) | models.Q(assigned_to_id=c.user_id)
            ).count(),
        } for c in clients]
        return JsonResponse({'clients': data}, status=200)  


#cusotmers with their gateways
@csrf_exempt
def get_all_customers_for_superadmin(request):
    if request.method == 'GET':
        try:
            customers = User.objects.filter(
                usertype__name='Customer'
            ).select_related('parent')

            data = []
            for cu in customers:
                gateways = GatewayRelational.objects.filter(
                    user=cu
                ).select_related('gateway', 'gateway__project')

                data.append({
                    'user_id': cu.user_id,
                    'username': cu.username,
                    'email': cu.email,
                    'client_name': cu.parent.username if cu.parent else "N/A",
                    'gateway_count': gateways.count(),
                    'gateways': [r.gateway.gateway_name for r in gateways],
                    'projects': [
                        {
                            'project_id': r.gateway.project.project_id,
                            'project_name': r.gateway.project.project_name,
                            'gateway_name': r.gateway.gateway_name,
                        }
                        for r in gateways
                        if r.gateway.project
                    ],
                })

            return JsonResponse({'customers': data}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)  
        
#all projects      
@csrf_exempt
def get_all_projects_for_superadmin(request):
    if request.method == 'GET':
        try:
            projects = Project.objects.all().select_related('user', 'assigned_to')
            data = [{
                'project_id': p.project_id,
                'project_name': p.project_name,
                'project_address': p.project_address,
                'client_name': p.user.username if p.user else 'N/A',
                'assigned_to_username': p.assigned_to.username if p.assigned_to else 'N/A',
                'assigned_to_id': p.assigned_to.user_id if p.assigned_to else None,
                'gateway_count': p.gateways.count(),
                'created_at': str(p.created_at) if p.created_at else None,
                'deployed_status': p.deployed_status,
            } for p in projects]
            return JsonResponse({'projects': data}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def delete_admin(request, admin_id):
    if request.method == 'DELETE':
        try:
            user = User.objects.get(user_id=admin_id)
            user.delete()
            return JsonResponse({'message': 'Admin deleted!'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Admin not found'}, status=404)
        
@csrf_exempt
def delete_user(request, user_id):
   
    if request.method == 'DELETE':
        try:
            user = User.objects.get(user_id=user_id)
            role = user.usertype.name if user.usertype else ''

            # ── ADMIN 
            if role == 'Admin':
                remaining_clients = User.objects.filter(
                    parent_id=user_id,
                    usertype__name='Client'
                    
                ).count()
                if remaining_clients > 0:
                    return JsonResponse({
                        'error': f'Cannot delete admin. {remaining_clients} client(s) still assigned!'
                    }, status=400)

            # ── CLIENT ─
            elif role == 'Client':
                # Check customers
                remaining_customers = User.objects.filter(
                    parent_id=user_id,
                    usertype__name='Customer'
                ).count()
                if remaining_customers > 0:
                    return JsonResponse({
                        'error': f'Cannot delete client. {remaining_customers} customer(s) still assigned!'
                    }, status=400)

               

            # ── CUSTOMER 
            elif role == 'Customer':
                remaining_gateways = GatewayRelational.objects.filter(
                    user_id=user_id
                ).count()
                if remaining_gateways > 0:
                    return JsonResponse({
                        'error': f'Cannot delete customer. {remaining_gateways} gateway(s) still assigned!'
                    }, status=400)

    
            user.delete()
            return JsonResponse({'message': f'{role} deleted successfully!'}, status=200)

        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def reassign_clients_to_admin(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        old_admin_id = data.get('old_admin_id')
        new_admin_id = data.get('new_admin_id')
        try:
            new_admin = User.objects.get(user_id=new_admin_id)
            updated = User.objects.filter(
                parent_id=old_admin_id,
                usertype__name__iexact='Clinet'
            ).update(parent=new_admin)
            return JsonResponse({
                'message': f'{updated} clients reassigned to {new_admin.username}!'
            }, status=200)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Admin not found'}, status=404)
        
@csrf_exempt
def reassign_customers_to_client(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        old_client_id = data.get('old_client_id')
        new_client_id = data.get('new_client_id')
        try:
            new_client = User.objects.get(user_id=new_client_id)
            User.objects.filter(
                parent_id=old_client_id,
                usertype__name='Customer'
            ).update(parent=new_client)
            return JsonResponse({'message': 'Customers reassigned!'}, status=200)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Client not found'}, status=404)
        

@csrf_exempt
def reassign_gateways_to_customer(request):
  
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            old_customer_id = data.get('old_customer_id')
            new_customer_id = data.get('new_customer_id')

            new_customer = User.objects.get(user_id=new_customer_id)

            updated = GatewayRelational.objects.filter(
                user_id=old_customer_id
            ).update(user=new_customer)

            return JsonResponse({
                'message': f'{updated} gateways reassigned to {new_customer.username}!'
            }, status=200)
        except User.DoesNotExist:
            return JsonResponse({'error': 'New customer not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def reassign_gateways_to_project(request):
   
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            old_project_id = data.get('old_project_id')
            new_project_id = data.get('new_project_id')

            new_project = Project.objects.get(project_id=new_project_id)

            updated = Gateway.objects.filter(
                project_id=old_project_id
            ).update(project=new_project)

            return JsonResponse({
                'message': f'{updated} gateways reassigned to {new_project.project_name}!'
            }, status=200)
        except Project.DoesNotExist:
            return JsonResponse({'error': 'New project not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
@csrf_exempt
def reassign_projects_to_client(request):
   
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            old_client_id = data.get('old_client_id')
            new_client_id = data.get('new_client_id')

            with transaction.atomic():
                new_client = User.objects.get(user_id=new_client_id)

                projects = Project.objects.filter(user_id=old_client_id)
                count = projects.count()

                for project in projects:
                    project.user = new_client
                    project.save()

                # Verify
                remaining = Project.objects.filter(user_id=old_client_id).count()
                if remaining > 0:
                    raise Exception(f'{remaining} projects could not be reassigned!')

            return JsonResponse({
                'message': f'{count} project(s) reassigned to {new_client.username} successfully!'
            }, status=200)

        except User.DoesNotExist:
            return JsonResponse({'error': 'New client not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)



@csrf_exempt
def delete_project(request, project_id):
   
    if request.method == 'DELETE':
        try:
            project = Project.objects.get(project_id=project_id)
            project.delete()
            return JsonResponse({'message': 'Project deleted!'}, status=200)
        except Project.DoesNotExist:
            return JsonResponse({'error': 'Project not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def get_all_usertypes(request):
    if request.method == 'GET':
        types = UserType.objects.all()
        data = [{'usertype_id': t.usertype_id, 'name': t.name} for t in types]
        return JsonResponse({'usertypes': data}, status=200)


@csrf_exempt
def get_all_users(request):
    if request.method == 'GET':
        users = User.objects.select_related('usertype').all()
        data = [{
            'user_id': u.user_id,
            'username': u.username,
            'email': u.email,
            'usertype_name': u.usertype.name if u.usertype else None,
        } for u in users]
        return JsonResponse({'users': data}, status=200)


#  CLIENTs customers full detail
def client_my_customers(request, client_id):
    if request.method == 'GET':
        customers = User.objects.filter(
            parent_id=client_id,
            usertype__name='Customer'
        ).select_related('parent')
        data = []
        for cu in customers:
            gateways = GatewayRelational.objects.filter(
                user=cu,
                relation_type='customer',
            ).select_related('gateway', 'gateway__project')
            data.append({
                'user_id': cu.user_id,
                'username': cu.username,
                'email': cu.email,
                'client_name': cu.parent.username if cu.parent else 'N/A',
                'gateway_count': gateways.count(),
                'gateways': [
                    {
                        **gateway_to_dict(r.gateway),
                        'relation_active_status': r.active_status,
                        'relation_last_hit_timestamp': r.last_hit_timestamp.isoformat() if r.last_hit_timestamp else None,
                    }
                    for r in gateways
                ],
                'projects': [
                    {
                        'gateway_name': r.gateway.gateway_name,
                        'project_name': r.gateway.project.project_name,
                        'project_id': r.gateway.project.project_id,
                    }
                    for r in gateways
                    if r.gateway.project
                ],
            })
        return JsonResponse({'customers': data}, status=200)  
    
    
#clients proejct   
@csrf_exempt
def client_my_projects(request, client_id):
    if request.method == 'GET':
        projects = Project.objects.filter(
            models.Q(user_id=client_id) | models.Q(assigned_to_id=client_id)
        ).select_related('user', 'assigned_to').prefetch_related('gateways')
        
        data = [{
            'project_id': p.project_id,
            'project_name': p.project_name,
            'project_address': p.project_address,
            'gateway_count': p.gateways.count(),
            'assigned_to_username': p.assigned_to.username if p.assigned_to else 'N/A',
            'created_at': str(p.created_at) if p.created_at else None,
            'deployed_status': p.deployed_status,
        } for p in projects]
        return JsonResponse({'projects': data}, status=200)





#clients specific project gateways
@csrf_exempt
def client_project_gateways(request, client_id, project_id):
    if request.method == 'GET':
        project = Project.objects.filter(
            project_id=project_id,
        ).filter(
            models.Q(user_id=client_id) | models.Q(assigned_to_id=client_id)
        ).first()

        if not project:
            return JsonResponse({'error': 'Project not found'}, status=404)

        gateways = Gateway.objects.filter(project=project).select_related(
            'project', 'project__user',
            'gatewaytype', 'gatewaysubtype', 'deploy_status', 'active_status'
        ).prefetch_related('status_history')
        return JsonResponse({'gateways': [gateway_to_dict(g) for g in gateways]}, status=200)


#  CUSTOMER VIEWS



@csrf_exempt
def customer_gateway_detail(request, customer_id, gateway_id):
    if request.method == 'GET':
        relation = GatewayRelational.objects.filter(
            user_id=customer_id,
            gateway_id=gateway_id
        ).select_related('gateway').first()

        if not relation:
            relation = GatewayRelational.objects.filter(
                gateway_id=gateway_id
            ).select_related('gateway').order_by('-assigned_at', '-datetime').first()

        if relation:
            g = relation.gateway
        else:
            g = Gateway.objects.filter(gateway_id=gateway_id).first()

        if not g:
            return JsonResponse({'error': 'Gateway not found'}, status=404)
        sensors = g.sensors.select_related('sensortype').all()
        cameras = g.cameras.all()
        latest_metadata = g.metadata.order_by('-timestamp').first()
        metadata_json = latest_metadata.json_data if latest_metadata else {}
        metadata_history = g.metadata.order_by('-timestamp')[:100]

        # inject sensor_id dynamically
        if metadata_json:
            for key, items in metadata_json.items():

                if isinstance(items, list):
                    for item in items:
                        rf_id = str(item.get('rf_id'))
                        sensor = g.sensors.filter(sensor_rf_id=rf_id).first()
                        if sensor:
                            item['sensor_id'] = sensor.sensor_id

                elif isinstance(items, dict):
                    rf_id = str(items.get('rf_id'))
                    sensor = g.sensors.filter(sensor_rf_id=rf_id).first()
                    if sensor:
                        items['sensor_id'] = sensor.sensor_id

        def metadata_to_dict(item):
            return {
                'json_data': item.json_data,
                'timestamp': item.timestamp.isoformat() if item.timestamp else None,
                'posted_timestamp': item.posted_timestamp.isoformat() if item.posted_timestamp else None,
                'source_user_id': item.source_user_id,
                'device_battery': item.device_battery,
                'alert': item.alert,
                'warning': item.warning,
                'sensors_alert': item.sensors_alert,
                'cam_alert': item.cam_alert,
                'sensors_alert_count': item.sensors_alert_count,
                'cam_alert_count': item.cam_alert_count,
                'location': item.location,
                'phones': item.phones,
                'sensors_alert_events': item.sensors_alert_events,
                'cam_alert_events': item.cam_alert_events,
                'arm': item.arm,
            }

        return JsonResponse({
            'gateway_id'  : g.gateway_id,
            'gateway_name': g.gateway_name,
            'mac_address' : g.gateway_mac_address,
            'imei'        : g.gateway_imei,
            'ssid'        : g.gateway_ssid,
            'longitude'   : str(g.gateway_longitude) if g.gateway_longitude else None,
            'latitude'    : str(g.gateway_latitude)  if g.gateway_latitude  else None,
            'project_name' : g.project.project_name if g.project else 'N/A',
            'project_address': g.project.project_address if g.project else 'N/A',
            'gateway_type' : g.gatewaytype.name if g.gatewaytype else None,
            'gateway_subtype' : g.gatewaysubtype.name if g.gatewaysubtype else None,
            'deploy_status': g.deploy_status.name if g.deploy_status else None,
            'active_status': g.active_status.name if g.active_status else 'not_connected',
            'last_seen'    : g.last_seen.isoformat() if g.last_seen else None,
            'last_hit_timestamp': relation.last_hit_timestamp.isoformat() if relation and relation.last_hit_timestamp else None,
            'relation_active': relation.active_status if relation else False,
            'relation_user_id': relation.user_id if relation else None,

            # ── Sensors with rf_id and sensortype ──
            'sensors': [
                {
                    'id'        : s.sensor_id,
                    'name'      : s.sensor_name,
                    'rf_id'     : s.sensor_rf_id or '—',
                    'sensortype': s.sensortype.name if s.sensortype else 'unknown',
                }
                for s in sensors
            ],

            'cameras': [
                {
                    'id'  : c.cam_id,
                    'name': c.cam_name,
                    'url' : c.cam_url,
                    'rf_id': c.cam_rf_id,
                }
                for c in cameras
            ],

            'latest_metadata': {
                **metadata_to_dict(latest_metadata),
                'json_data': metadata_json
            } if latest_metadata else None,   
            'metadata_history': [metadata_to_dict(item) for item in reversed(metadata_history)],

        }, status=200)

    return JsonResponse({'error': 'Method not allowed'}, status=405)



  
  
  
        
@csrf_exempt
def update_gateway(request, gateway_id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            gateway = Gateway.objects.get(gateway_id=gateway_id)

            for field in ['gateway_name', 'gateway_static_id', 'gateway_password',
                          'gateway_ssid', 'gateway_mac_address', 'gateway_imei',
                          'gateway_static_wifi', 'gateway_wifi_ssid',
                          'gateway_wifi_password', 'gateway_longitude', 'gateway_latitude']:
                if field in data:
                    setattr(gateway, field, data[field])

            if 'project_id' in data:
                gateway.project = Project.objects.get(project_id=data['project_id'])

            if 'gatewaytype_id' in data:
                gateway.gatewaytype = GatewayType.objects.get(
                    gatewaytype_id=data['gatewaytype_id']
                ) if data['gatewaytype_id'] else None

            if 'gatewaysubtype_id' in data:
                gateway.gatewaysubtype = GatewaySubType.objects.get(
                    gatewaysubtype_id=data['gatewaysubtype_id'],
                    gatewaytype=gateway.gatewaytype,
                ) if data['gatewaysubtype_id'] else None

            gateway.save()

            if any(k in data for k in ['deployment_status', 'allotted_to_client', 'allotted_to_customer']):
                deployment_status = data.get('deployment_status')
                allotted_client = None
                if data.get('allotted_to_client'):
                    allotted_client = User.objects.get(user_id=data['allotted_to_client'])
                    deployment_status = deployment_status or 'assign_to_client'

                allotted_customer = None
                if data.get('allotted_to_customer'):
                    allotted_customer = User.objects.get(user_id=data['allotted_to_customer'])
                    deployment_status = deployment_status or 'assign_to_customer'

                deployment_status = deployment_status or 'deploy_to_warehouse'
                gateway.deploy_status = get_deploy_status(deployment_status)
                gateway.save(update_fields=['deploy_status'])

                GatewayStatus.objects.create(
                    gateway=gateway,
                    deployment_status=deployment_status,
                    allotted_to_client=allotted_client,
                    allotted_to_customer=allotted_customer,
                )

            return JsonResponse({
                "message": "Gateway updated!",
                **gateway_to_dict(gateway)
            }, status=200)

        except Gateway.DoesNotExist:
            return JsonResponse({"error": "Gateway not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        
        
@csrf_exempt
def delete_gateway(request, gateway_id):
    if request.method == 'DELETE':
        try:
            Gateway.objects.get(gateway_id=gateway_id).delete()
            return JsonResponse({'message': 'Gateway deleted!'}, status=200)
        except Gateway.DoesNotExist:
            return JsonResponse({'error': 'Gateway not found'}, status=404)

#all gateways
@csrf_exempt
def get_all_gateways_for_superadmin(request):
    if request.method == 'GET':
        gateways = Gateway.objects.all().select_related(
            'project', 'gatewaytype', 'gatewaysubtype', 'deploy_status', 'active_status'
        ).prefetch_related('status_history')
        return JsonResponse({'gateways': [gateway_to_dict(g) for g in gateways]}, status=200)

 
@csrf_exempt
def get_gateway_types(request):
    if request.method == 'GET':
        types = GatewayType.objects.filter(name__in=['MC', 'MS']).prefetch_related('subtypes').order_by('name')
        return JsonResponse({
            'gatewaytypes': [
                {
                    'gatewaytype_id': t.gatewaytype_id,
                    'name': t.name,
                    'description': t.description,
                    'subtypes': [
                        {
                            'gatewaysubtype_id': st.gatewaysubtype_id,
                            'name': st.name,
                            'description': st.description,
                        }
                        for st in t.subtypes.all()
                    ],
                }
                for t in types
            ]
        }, status=200)

#list for dropdown
@csrf_exempt
def client_customers_list(request, client_id):
    if request.method == 'GET':
        customers = User.objects.filter(parent_id=client_id, usertype__name='Customer')
        return JsonResponse({'customers': [{'user_id': c.user_id, 'username': c.username, 'email': c.email} for c in customers]}, status=200)


@csrf_exempt
def create_customer(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            client_code = data.get('client_code')
            client_id = data.get('client_id')     
            gateway_id = data.get('gateway_id')

            if client_code:
                try:
                    client = User.objects.get(client_code=client_code, usertype__name='Client')
                except User.DoesNotExist:
                    return JsonResponse({'error': 'Invalid client code'}, status=400)
            elif client_id:
                try:
                    client = User.objects.get(user_id=int(client_id), usertype__name='Client')
                except User.DoesNotExist:
                    return JsonResponse({'error': 'Client not found'}, status=400)
            else:
                return JsonResponse({'error': 'client_code or client_id is required'}, status=400)

            customer_role = UserType.objects.filter(name='Customer').first()
            if not customer_role:
                return JsonResponse({'error': 'Customer role not found'}, status=400)

            if User.objects.filter(username=data.get('username')).exists():
                return JsonResponse({'error': 'Username already exists'}, status=400)

            if User.objects.filter(email=data.get('email')).exists():
                return JsonResponse({'error': 'Email already exists'}, status=400)

            with transaction.atomic():
                customer = User.objects.create(
                    username=data.get('username'),
                    userpass=data.get('password'),
                    email=data.get('email'),
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name'),
                    phone_number=data.get('phone_number'),
                    address=data.get('address'),
                    icon=data.get('image'),
                    usertype=customer_role,
                    parent=client,
                )

                if gateway_id:
                    try:
                        gateway = Gateway.objects.get(gateway_id=int(gateway_id))
                        valid, error = validate_gateway_customer_assignment(gateway, customer)
                        if not valid:
                            return JsonResponse({'error': error}, status=400)
                        GatewayRelational.objects.create(
                            user=customer,
                            gateway=gateway,
                            relation_type='customer',
                        )
                    except Gateway.DoesNotExist:
                        return JsonResponse({'error': 'Gateway not found'}, status=404)

            return JsonResponse({
                'message': 'Customer created!',
                'user_id': customer.user_id,
                'username': customer.username,
                'linked_to_client': client.username,
            }, status=201)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)   
        
        
       
@csrf_exempt
def admin_available_gateways(request, client_id):
    if request.method == 'GET':
        try:
            client = User.objects.get(user_id=client_id, usertype__name='Client')
            admin = client.parent

            if not admin:
                return JsonResponse({'error': 'Admin not found for this client'}, status=404)

            assigned_gateway_ids = GatewayRelational.objects.filter(
                relation_type='customer'
            ).values_list('gateway_id', flat=True)

            gateways = Gateway.objects.filter(
                models.Q(project__assigned_to_id=client.user_id) |
                models.Q(project__user_id=client.user_id)
            ).exclude(
                gateway_id__in=assigned_gateway_ids  
            ).select_related('project', 'gatewaytype', 'gatewaysubtype', 'deploy_status', 'active_status')

            data = [gateway_to_dict(g) for g in gateways]

            return JsonResponse({'gateways': data}, status=200)

        except User.DoesNotExist:
            return JsonResponse({'error': 'Client not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        
@csrf_exempt
def update_customer(request, customer_id):
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            customer = User.objects.get(user_id=customer_id)

            if 'username' in data and data['username'] != customer.username:
                if User.objects.filter(username=data['username']).exists():
                    return JsonResponse({'error': 'Username already exists'}, status=400)
                customer.username = data['username']

            if 'email' in data and data['email'] != customer.email:
                if User.objects.filter(email=data['email']).exists():
                    return JsonResponse({'error': 'Email already exists'}, status=400)
                customer.email = data['email']

            if data.get('password'):
                customer.userpass = data['password']

            customer.save()
            return JsonResponse({
                'message': 'Customer updated!',
                'user_id': customer.user_id,
                'username': customer.username,
            }, status=200)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Customer not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
@csrf_exempt
def update_client(request, client_id):
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            client = User.objects.get(user_id=client_id)

            if 'username' in data and data['username'] != client.username:
                if User.objects.filter(username=data['username']).exists():
                    return JsonResponse({'error': 'Username already exists'}, status=400)
                client.username = data['username']

            if 'email' in data and data['email'] != client.email:
                if User.objects.filter(email=data['email']).exists():
                    return JsonResponse({'error': 'Email already exists'}, status=400)
                client.email = data['email']

            if 'first_name' in data:
                client.first_name = data['first_name']
            if 'last_name' in data:
                client.last_name = data['last_name']
            if 'phone_number' in data:
                client.phone_number = data['phone_number']
            if 'address' in data:
                client.address = data['address']
            if data.get('password'):
                client.userpass = data['password']

            # ── Naye fields ──
            if 'icon' in data:
                client.icon = data['icon']

            if 'usertype_id' in data:
                try:
                    from .models import UserType
                    client.usertype = UserType.objects.get(usertype_id=data['usertype_id'])
                except UserType.DoesNotExist:
                    return JsonResponse({'error': 'Invalid usertype'}, status=400)

            if 'parent_id' in data:
                try:
                    client.parent = User.objects.get(user_id=data['parent_id'])
                except User.DoesNotExist:
                    return JsonResponse({'error': 'Parent user not found'}, status=400)

            client.save()
            return JsonResponse({
                'message': 'User updated successfully!',
                'user_id': client.user_id,
                'username': client.username,
                'email': client.email,
                'icon': client.icon or '',
                'usertype_id': client.usertype.usertype_id if client.usertype else None,
                'parent_id': client.parent.user_id if client.parent else None,
            }, status=200)

        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)








@csrf_exempt
def receive_gateway_data(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    mac_address = body.get('mac_address', '').strip().upper()

    if not mac_address:
        return JsonResponse({'error': 'mac_address is required'}, status=400)

    try:
        gateway = Gateway.objects.get(gateway_mac_address__iexact=mac_address)
        sensors = Sensor.objects.filter(gateway=gateway)

        sensor_map = {
            str(s.sensor_rf_id): s.sensor_id
            for s in sensors if s.sensor_rf_id
        }
    except Gateway.DoesNotExist:
        return JsonResponse({'device_status': 'not_connected', 'message': 'Device not registered'}, status=404)

    hit_fields = extract_gateway_hit_fields(body)

    relations = GatewayRelational.objects.filter(
        gateway=gateway
    ).select_related('user')

    if hit_fields['source_user_id']:
        relations = relations.filter(user_id=hit_fields['source_user_id'])

    if not relations.exists():
        return JsonResponse({'error': 'Unauthorized: No user linked to this gateway'}, status=403)

    status_obj, _ = GatewayStatusType.objects.get_or_create(
        status_id=1,
        defaults={'description': 'Online'}
    )

    now = timezone.now()
    active_status_name = classify_gateway_payload(body)
    active_status = get_active_status(active_status_name)
    user_ids = []
    for relation in relations:
        relation.status = status_obj
        relation.datetime = now
        relation.last_hit_timestamp = now
        relation.active_status = True
        relation.save(update_fields=['status', 'datetime', 'last_hit_timestamp', 'active_status'])
        user_ids.append(relation.user.user_id)

    arm_status = body.get('status', '').lower() == 'arm'

    gateway.last_seen  = now
    gateway.arm_status = 'arm' if arm_status else 'disarm'
    gateway.active_status = active_status
    gateway_update_fields = ['last_seen', 'arm_status', 'active_status']
    location = hit_fields.get('location') or {}
    if location.get('longitude') not in [None, '']:
        gateway.gateway_longitude = location.get('longitude')
        gateway_update_fields.append('gateway_longitude')
    if location.get('latitude') not in [None, '']:
        gateway.gateway_latitude = location.get('latitude')
        gateway_update_fields.append('gateway_latitude')
    gateway.save(update_fields=gateway_update_fields)

    hit_fields['warning'] = active_status_name == 'connected_wrong_data_found'

    

    metadata_body = body.get('metadata', {})
    if not isinstance(metadata_body, dict):
        metadata_body = {}
    cams_data = metadata_body.get('cams', {})

    SENSOR_TYPE_MAP = {
        'DW_sensors':       'DW_sensors',
        'lpg':              'lpg',
        'smoke':            'smoke',
        'motion_detection': 'motion_detection',
        'human_appearance': 'human_appearance',
    }

    for json_key, sensortype_name in SENSOR_TYPE_MAP.items():
        sensors_list = metadata_body.get(json_key, [])
        sensortype, _ = SensorType.objects.get_or_create(name=sensortype_name)

        for s in sensors_list:
            rf_id = str(s.get('rf_id', '')).strip()
            name  = s.get('name', sensortype_name)
            value = s.get('Value')

            if rf_id:
                sensor_obj, _ = Sensor.objects.update_or_create(
                    gateway=gateway,
                    sensor_rf_id=rf_id,
                    defaults={'sensor_name': name, 'sensortype': sensortype, 'value': value}
                )
            else:
                sensor_obj, _ = Sensor.objects.update_or_create(
                    gateway=gateway,
                    sensor_name=name,
                    sensor_rf_id=None,
                    defaults={'sensortype': sensortype, 'value': value}
                )
            s["sensor_id"] = sensor_obj.sensor_id

            SensorHistory.objects.create(sensor=sensor_obj, value=value)

    burglar_data = metadata_body.get('burglar')
    if burglar_data:
        burglar_type, _ = SensorType.objects.get_or_create(name='burglar')
        rf_id = str(burglar_data.get('rf_id', '')).strip()
        value = burglar_data.get('Value')
        if rf_id:
            sensor_obj, _ = Sensor.objects.update_or_create(
                
                gateway=gateway,
                sensor_rf_id=rf_id,
                defaults={'sensor_name': 'Burglar', 'sensortype': burglar_type, 'value': value}
            )
        else:
            sensor_obj, _ = Sensor.objects.update_or_create(
                gateway=gateway,
                sensor_name='Burglar',
                sensor_rf_id=None,
                defaults={'sensortype': burglar_type, 'value': value}
            )
        burglar_data["sensor_id"] = sensor_obj.sensor_id
        SensorHistory.objects.create(sensor=sensor_obj, value=value)

    for cam_key, cam_info in cams_data.items():
        cam_name = cam_info.get('name') or cam_key
        cam_url  = cam_info.get('url') or None

        camera, _ = Camera.objects.update_or_create(
            gateway=gateway,
            cam_name=cam_name,
            defaults={'cam_url': cam_url}
        )

        rois = cam_info.get('configurations', {}).get('rois', [])
        for roi in rois:
            roi_name   = roi.get('roi_name', '')
            roi_coords = roi.get('roi_coordinates', '')
            enabled    = roi.get('enabled', True)
            if roi_name:
                CameraROI.objects.update_or_create(
                    camera=camera,
                    roi_name=roi_name,
                    defaults={'roi_coordinates': roi_coords, 'enabled': enabled}
                )
    print("===== METADATA BEFORE SAVE =====")
    print(body.get("metadata"))
    Metadata.objects.create(
        gateway=gateway,
        json_data=body,
        arm=arm_status,
        **hit_fields,
    )

    return JsonResponse({
        'device_status': active_status_name,
        'message': 'Device registered and data saved',
        'user_ids': user_ids,
        'data': body,
    }, status=200)









@csrf_exempt
def customer_my_gateways(request, customer_id):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)

    relations = GatewayRelational.objects.filter(
        user_id=customer_id,
        relation_type='customer',
    ).select_related(
        'gateway',
        'gateway__project',
        'gateway__gatewaytype',
        'gateway__gatewaysubtype',
        'gateway__deploy_status',
        'gateway__active_status',
    )

    data = []
    for rel in relations:
        g = rel.gateway

        meta_obj = g.metadata.order_by('-timestamp').first()
        latest_json = None
        if meta_obj and meta_obj.json_data:
            try:
                latest_json = meta_obj.json_data if isinstance(meta_obj.json_data, dict) else json.loads(meta_obj.json_data)
            except (json.JSONDecodeError, TypeError):
                latest_json = None

        data.append({
            'gateway_id'         : g.gateway_id,
            'gateway_name'       : g.gateway_name,
            'mac_address': g.gateway_mac_address,
            'project_name'       : g.project.project_name if g.project else 'N/A',
            'imei'               : g.gateway_imei,
            'address'            : g.project.project_address if g.project else 'N/A',
            'sensor_count'       : g.sensors.count(), 
            'alert'              : meta_obj.alert if meta_obj else None,
            'warning'            : meta_obj.warning if meta_obj else None,
            'sensors_alert'      : meta_obj.sensors_alert if meta_obj else None,
            'cam_alert'          : meta_obj.cam_alert if meta_obj else None,
            'sensors_alert_count': meta_obj.sensors_alert_count if meta_obj else 0,
            'cam_alert_count'    : meta_obj.cam_alert_count if meta_obj else 0,
            'device_battery'     : meta_obj.device_battery if meta_obj else None,
            'posted_timestamp'   : meta_obj.posted_timestamp.isoformat() if meta_obj and meta_obj.posted_timestamp else None,
            'phones'             : meta_obj.phones if meta_obj else None,
            'deploy_status'      : g.deploy_status.name if g.deploy_status else None,
            'gateway_type'       : g.gatewaytype.name if g.gatewaytype else None,
            'gateway_subtype'    : g.gatewaysubtype.name if g.gatewaysubtype else None,
            'active_status'      : g.active_status.name if g.active_status else 'not_connected',
            'last_hit_timestamp' : rel.last_hit_timestamp.isoformat() if rel.last_hit_timestamp else None,
            'last_seen'          : g.last_seen.isoformat() if g.last_seen else None,
            **( latest_json if isinstance(latest_json, dict) else {} )
})
    return JsonResponse({'gateways': data}, status=200)




def check_gateway_status(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)

    mac_address = request.GET.get('mac_address', '').strip().upper()
    user_id = request.GET.get('user_id')
    

    if not mac_address:
        return JsonResponse({'error': 'mac_address is required'}, status=400)

    if not user_id:
        return JsonResponse({'error': 'user_id is required'}, status=400)

    try:
        gateway = Gateway.objects.get(gateway_mac_address__iexact=mac_address)
    except Gateway.DoesNotExist:
        return JsonResponse({
            'device_status': 'not_connected',
            'message': 'Device not registered'
        }, status=404)

    relation = GatewayRelational.objects.filter(
        gateway=gateway,
        user__user_id=user_id
    ).first()

    if not relation:
        return JsonResponse({
            'error': 'Unauthorized: This gateway does not belong to this user'
        }, status=403)

    if gateway.last_seen is None:
        return JsonResponse({
            'device_status': 'not_connected',
            'message': 'Device never posted data yet'
        }, status=200)

    if gateway.last_seen and timezone.now() - gateway.last_seen > timedelta(minutes=30):
        device_status = 'not_connected'
        relation.active_status = False
        relation.save(update_fields=['active_status'])
        gateway.active_status = get_active_status(device_status)
        gateway.save(update_fields=['active_status'])
    elif gateway.active_status:
        device_status = gateway.active_status.name
    elif gateway.metadata.exists():
        device_status = 'connected_data_found'
    else:
        device_status = 'connected_no_data_found'

    return JsonResponse({
        'gateway_name': gateway.gateway_name,
        'mac_address': gateway.gateway_mac_address,
        'device_status': device_status,
        'deploy_status': gateway.deploy_status.name if gateway.deploy_status else None,
        'relation_active': relation.active_status,
        'last_hit_timestamp': relation.last_hit_timestamp.isoformat() if relation.last_hit_timestamp else None,
        'last_seen': gateway.last_seen.isoformat() if gateway.last_seen else None,
    }, status=200)
 
 

@csrf_exempt
def run_system_checks(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)

    expected_key = os.environ.get('VMS_SYSTEM_CHECK_KEY', 'dev-secret')
    provided_key = request.headers.get('X-System-Check-Key')
    if expected_key and provided_key != expected_key:
        return JsonResponse({'error': 'Unauthorized system check request'}, status=401)

    try:
        timeout_minutes = int(request.GET.get('timeout_minutes', 30))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'timeout_minutes must be an integer'}, status=400)

    if timeout_minutes < 1:
        return JsonResponse({'error': 'timeout_minutes must be greater than 0'}, status=400)

    cutoff = timezone.now() - timedelta(minutes=timeout_minutes)
    offline_status = get_active_status('not_connected')

    stale_gateway_q = (
        models.Q(last_seen__lt=cutoff) |
        models.Q(last_seen__isnull=True)
    )
    stale_gateways = Gateway.objects.filter(stale_gateway_q).exclude(active_status=offline_status)
    stale_gateway_ids = list(stale_gateways.values_list('gateway_id', flat=True))
    gateway_count = stale_gateways.update(active_status=offline_status)

    stale_relation_q = (
        models.Q(last_hit_timestamp__lt=cutoff) |
        models.Q(last_hit_timestamp__isnull=True)
    )
    stale_relations = GatewayRelational.objects.filter(
        stale_relation_q,
        active_status=True,
    )
    stale_relation_ids = list(stale_relations.values_list('gatewayrelational_id', flat=True))
    relation_count = stale_relations.update(active_status=False)

    return JsonResponse({
        'status': 'completed',
        'checks': {
            'gateways': {
                'timeout_minutes': timeout_minutes,
                'cutoff': cutoff.isoformat(),
                'marked_not_connected': gateway_count,
                'gateway_ids': stale_gateway_ids,
            },
            'gateway_relations': {
                'marked_inactive': relation_count,
                'gatewayrelational_ids': stale_relation_ids,
            },
            'invoices': {
                'status': 'reserved_for_next_version',
            },
            'project_controls': {
                'status': 'reserved_for_next_version',
            },
        }
    }, status=200)





   
@csrf_exempt
def update_device_status(request):
    if request.method == "PUT":
        try:
            # ---------- PARSE JSON ----------
            try:
                data = json.loads(request.body.decode("utf-8"))
            except Exception:
                return JsonResponse({
                    "success": False,
                    "message": "Invalid body"
                }, status=400)

            gateway_id = data.get("gateway_id")
            status = (data.get("status") or "").strip().lower()

            # ---------- VALIDATION ----------
            if not gateway_id:
                return JsonResponse({
                    "success": False,
                    "message": "gateway_id is required"
                }, status=400)

            if status not in ["arm", "disarm"]:
                return JsonResponse({
                    "success": False,
                    "message": "status must be 'arm' or 'disarm'"
                }, status=400)

            # ---------- GET SINGLE DEVICE ----------
            device = Gateway.objects.filter(gateway_id=gateway_id).first()

            if not device:
                return JsonResponse({
                    "success": False,
                    "message": "Device not found in database"
                }, status=404)

            # ---------- ALREADY SAME STATUS CHECK ----------
            if device.arm_status == status:
                return JsonResponse({
                    "success": False,
                    "message": f"Device is already {status}ed",
                    "data": {
                        "status": device.arm_status
                    }
                }, status=400)

            # ---------- UPDATE STATUS ONLY ----------
            device.arm_status = status
            device.save(update_fields=["arm_status"])

            # ---------- RESPONSE ----------
            return JsonResponse({
                "success": True,
                "message": f"Device {status}ed successfully",
                "data": {
                    "status": device.arm_status
                }
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": "Unexpected error",
                "error": str(e)
            }, status=500)

    return JsonResponse({
        "message": "invalid request method"
    })
    
@csrf_exempt
def receive_metadata(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    mac_address = body.get('mac_address', '').strip()

    if not mac_address:
        return JsonResponse({'error': 'mac_address is required'}, status=400)

    try:
        gateway = Gateway.objects.get(gateway_mac_address__iexact=mac_address)
    except Gateway.DoesNotExist:
        return JsonResponse({
            'device_status': 'not_connected',
            'message': 'Gateway not found in database'
        }, status=404)

    relations = GatewayRelational.objects.filter(  
        gateway=gateway
    ).select_related('user')

    if not relations.exists():
        return JsonResponse({
            'error': 'Unauthorized: No user is linked to this gateway'
        }, status=403)

    now = timezone.now()
    active_status_name = classify_gateway_payload(body)
    active_status = get_active_status(active_status_name)
    user_ids = []
    for relation in relations:
        relation.datetime = now
        relation.last_hit_timestamp = now
        relation.active_status = True
        relation.save(update_fields=['datetime', 'last_hit_timestamp', 'active_status'])
        user_ids.append(relation.user.user_id)
 
    arm_status = body.get('status', '').lower() == 'arm'
    gateway.last_seen = now
    gateway.arm_status = 'arm' if arm_status else 'disarm'
    gateway.active_status = active_status
    gateway.save(update_fields=['last_seen', 'arm_status', 'active_status'])

    Metadata.objects.create(
        gateway=gateway,
        json_data=body,
        arm=arm_status,
    )

    return JsonResponse({
        'device_status': active_status_name,
        'message': 'Metadata saved successfully',
        'user_ids': user_ids,
        'data': body
    }, status=201)
  
  
  
    
@csrf_exempt
@api_view(['GET'])
def get_gateway_sensors(request, gateway_id):

    sensors = Sensor.objects.filter(
        gateway_id=gateway_id
    ).select_related('sensortype')

    return Response({
        "success": True,
        "gateway_id": gateway_id,
        "sensor_count": sensors.count(),
        "sensors": [
            {
                "sensor_id": sensor.sensor_id,
                "sensor_name": sensor.sensor_name,
                "sensor_rf_id": sensor.sensor_rf_id,
                "sensor_type_id": sensor.sensortype.sensortype_id if sensor.sensortype else None,
                "sensor_type": sensor.sensortype.name if sensor.sensortype else None
            }
            for sensor in sensors
        ]
    })
    
    
@csrf_exempt
def get_sensor_by_id(request, sensor_id):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)
    
    try:
        sensor = Sensor.objects.select_related('sensortype', 'gateway').get(sensor_id=sensor_id)
    except Sensor.DoesNotExist:
        return JsonResponse({'error': f'Sensor with id {sensor_id} not found'}, status=404)

    history = SensorHistory.objects.filter(sensor=sensor).order_by('recorded_at')

    return JsonResponse({
        'success': True,
        'sensor': {
            'sensor_id':   sensor.sensor_id,
            'name':        sensor.sensor_name,
            'rf_id':       sensor.sensor_rf_id,
            'value':       sensor.value,
         
            'updated_at':  sensor.updated_at.isoformat(),
        },
        'total': history.count(),
        'history': [
            {
                'value':       h.value,
                'recorded_at': h.recorded_at.isoformat(),
            }
            for h in history
        ]
    }, status=200)




def health_check(request):
    return JsonResponse({
        "status": "online",
        "message": "API is running"
    })