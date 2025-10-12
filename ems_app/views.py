import uuid
from django.db import IntegrityError
from django.utils import timezone
from datetime import datetime
from django.forms import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import E1, E2, Com1, Com2, User , Project ,Hardware , User_Project , Project_Manager,Box, Device, Gateway,Gateways,Analyzer,Com1 , Com2 , E1 ,E2,MetaData, admincr, superadmincr, InvoiceTable
import json
from collections import defaultdict
from rest_framework import permissions
from django.db.models import Max
from django.utils.dateparse import parse_date
from django.utils import timezone
from datetime import datetime,timedelta
from datetime import timedelta  
from .models import Subscription, User
from datetime import datetime, timedelta 
from django.http import JsonResponse, HttpRequest
from django.utils.timezone import make_aware
import logging
import base64
from django.views import View
from rest_framework.decorators import api_view,  permission_classes

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
# from django.core.files.uploadedfile import InMemoryUploadedFile
# from django.core.files.storage import default_storage
from rest_framework.response import Response


from .models import SensorGateway, Sensor
from .serializers import GatewaySerializer, GatewaysSerializer, SensorSerializer
from django.http import JsonResponse
from .models import Gateway




@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def save_gateway_data(request):
    try:
        data = json.loads(request.body.decode('utf-8'))

        gateway_mac = data.get("GateWayMAC")

        # ✅ Step 1: Check if MAC exists in Gateways table
        existing_gateway = Gateways.objects.filter(mac_address=gateway_mac).first()
        if not existing_gateway:
            return JsonResponse({
                "success": False,
                "message": f"MAC address '{gateway_mac}' not found in Gateways table."
            }, status=404)

        # ✅ Step 2: Set gateway_id based on existing Gateways record
        gateway_id = existing_gateway.G_id

        # ✅ Step 3: Check if we already have a SensorGateway for this GateWayID
        gateway = SensorGateway.objects.filter(gateway_id=gateway_id).first()

        if gateway:
            print(f"⚙️ Gateway {gateway_id} already exists — updating sensors only.")
        else:
            print(f"🆕 Creating new SensorGateway for GateWayID: {gateway_id}.")
            gateway = SensorGateway.objects.create(
                gateway_id=gateway_id,
                gateway_mac=gateway_mac,
                alert_status=data.get("Alert_Status"),
                warning_status=data.get("Warning_status"),
                arm=data.get("Arm"),
                address=data.get("address"),
                latitude=data.get("Lat_Log", ["", ""])[0],
                longitude=data.get("Lat_Log", ["", ""])[1],
            )

        # ✅ Step 4: Save or update sensor data
        meta_data = data.get("Meta_Data", [])
        for sensor in meta_data:
            Sensor.objects.update_or_create(
                gateway=gateway,
                sensor_id=sensor.get("SID"),
                defaults={
                    "sensor_type": sensor.get("Sensor"),
                    "mac_id": sensor.get("MID"),
                    "sensor_name": sensor.get("Uname"),
                    "status": sensor.get("status"),
                    "battery": sensor.get("battery"),
                    "rf_status": sensor.get("rf"),
                    "enabled": True,
                },
            )

        return JsonResponse({
            "success": True,
            "message": f"Sensor data saved successfully for Gateway ID {gateway_id}."
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_gateway_sensors(request):
    """
    Fetch gateway and its sensors using gateway_id or gateway_mac
    URL: /api/getgatewaydata/?gateway_id=102 or /api/getgatewaydata/?mac=0398740384089
    """
    gateway_id = request.GET.get('gateway_id')
    mac = request.GET.get('mac')

    if not gateway_id and not mac:
        return JsonResponse({'success': False, 'message': 'Provide gateway_id or mac in query params'}, status=400)

    try:
        # Get gateway by ID or MAC
        if gateway_id:
            gateway = SensorGateway.objects.get(gateway_id=gateway_id)
        else:
            gateway = SensorGateway.objects.get(gateway_mac=mac)

        # Get all sensors for this gateway
        sensors = gateway.sensors.all()  # uses related_name="sensors"

        sensor_list = []
        for s in sensors:
            sensor_list.append({
                "Sensor": s.sensor_type,
                "SID": s.sensor_id,
                "MID": s.mac_id,
                "Uname": s.sensor_name,
                "status": s.status,
                "battery": s.battery,
                "rf": s.rf_status,
                "enabled": s.enabled,
                "image_url": s.image_url,  
            })

        # Prepare response
        response_data = {
            "success": True,
            "gateway_id": gateway.gateway_id,
            "gateway_mac": gateway.gateway_mac,
            "alert_status": gateway.alert_status,
            "warning_status": gateway.warning_status,
            "arm": gateway.arm,
            "address": gateway.address,
            "Lat_Log": [gateway.latitude, gateway.longitude],
            "Meta_Data": sensor_list
        }

        return JsonResponse(response_data, status=200)

    except SensorGateway.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Gateway not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)








@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_admincr(request):
    if request.method == 'POST':
        try:
            # Parse incoming JSON data
            data = json.loads(request.body)

            # Extract data from the request body
            cr_id = data.get('cr_id')
            admin_id = data.get('admin_id')

            # Basic validation for required fields
            if not cr_id or not admin_id:
                return JsonResponse({'error': 'cr_id and admin_id are required fields.'}, status=400)

            try:
                # Retrieve the superadmin instance by superadmin_id (check if superadmin_id exists)
                cr_id_instance = User.objects.get(user_id=cr_id_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User with the given cr_id_id does not exist.'}, status=404)

            # Ensure the su
                return JsonResponse({'error': 'The user does not have the required role (user).'}, status=403)

            try:
                # Retrieve the admin instance by admin_id (check if admin_id exists)
                admin_instance = User.objects.get(user_id=admin_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User with the given admin_id does not exist.'}, status=404)

            # Ensure the admin's role is 'admin'
            if admin_instance.role != 'admin':
                return JsonResponse({'error': 'The user does not have the required role (admin).'}, status=403)


            # Create a new admincr entry
            new_entry = admincr.objects.create(
                cr_id=cr_id,
                admin_id=admin_id
            )

            # Return the response with the created entry details
            return JsonResponse({
                'message': 'admincr entry created successfully',
                'sub_id': new_entry.sub_id,
                'cr_id': new_entry.cr_id,
                'admin_id': new_entry.admin_id
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid HTTP method. Use POST.'}, status=405)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_superadmincr(request):
    if request.method == 'POST':
        try:
            # Parse incoming JSON data
            data = json.loads(request.body)

            # Extract data from the request body
            superadmin_id = data.get('superadmin_id')
            admin_id = data.get('admin_id')

            # Basic validation for required fields
            if not superadmin_id or not admin_id:
                return JsonResponse({'error': 'superadmin_id and admin_id are required fields.'}, status=400)


            try:
                # Retrieve the superadmin instance by superadmin_id (check if superadmin_id exists)
                superadmin_instance = User.objects.get(user_id=superadmin_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User with the given superadmin_id does not exist.'}, status=404)

            # Ensure the superadmin's role is 'superadmin'
            if superadmin_instance.role != 'superadmin':
                return JsonResponse({'error': 'The user does not have the required role (superadmin).'}, status=403)

            try:
                # Retrieve the admin instance by admin_id (check if admin_id exists)
                admin_instance = User.objects.get(user_id=admin_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User with the given admin_id does not exist.'}, status=404)

            # Ensure the admin's role is 'admin'
            if admin_instance.role != 'admin':
                return JsonResponse({'error': 'The user does not have the required role (admin).'}, status=403)

            # Create a new superadmincr entry
            new_entry = superadmincr.objects.create(
                superadmin_id=superadmin_id,
                admin_id=admin_id
            )

            # Return the response with the created entry details
            return JsonResponse({
                'message': 'superadmincr entry created successfully',
                'sub_id': new_entry.sub_id,
                'superadmin_id': new_entry.superadmin_id,
                'admin_id': new_entry.admin_id
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid HTTP method. Use POST.'}, status=405)


@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def invoice_api(request):
    if request.method == 'GET':
        inv_id = request.GET.get('inv_id')

        if inv_id:
            try:
                invoice = InvoiceTable.objects.get(inv_id=inv_id)
                data = {
                    'inv_id': invoice.inv_id,
                    'subscription': invoice.subscription.sub_id,
                    'start_date': invoice.start_date,
                    'end_date': invoice.end_date,
                    'billing_price': float(invoice.billing_price),
                    'status': invoice.status
                }
                return JsonResponse(data)
            except InvoiceTable.DoesNotExist:
                return JsonResponse({'error': 'Invoice not found'}, status=404)
        else:
            invoices = InvoiceTable.objects.all()
            data = []
            for invoice in invoices:
                data.append({
                    'inv_id': invoice.inv_id,
                    'subscription': invoice.subscription.sub_id,
                    'start_date': invoice.start_date,
                    'end_date': invoice.end_date,
                    'billing_price': float(invoice.billing_price),
                    'status': invoice.status
                })
            return JsonResponse(data, safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            inv_id = data.get('inv_id')
            status = data.get('status')

            if not inv_id or not status:
                return JsonResponse({'error': 'inv_id and status are required'}, status=400)

            try:
                invoice = InvoiceTable.objects.get(inv_id=inv_id)
            except InvoiceTable.DoesNotExist:
                return JsonResponse({'error': 'Invoice not found'}, status=404)

            invoice.status = status
            invoice.save()

            return JsonResponse({
                'inv_id': invoice.inv_id,
                'subscription': invoice.subscription.sub_id,
                'start_date': invoice.start_date,
                'end_date': invoice.end_date,
                'billing_price': float(invoice.billing_price),
                'status': invoice.status,
                'message': 'Invoice status updated successfully'
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    else:
        return JsonResponse({'error': 'Unsupported HTTP method'}, status=405)


@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def create_or_update_subscription(request):
    if request.method == 'GET':
        try:
            # Fetch all subscriptions and related user data
            subscriptions = Subscription.objects.select_related('user_id').all()
            subscription_data = []
            print('user Creation',subscription_data)

            for sub in subscriptions:
                user = sub.user_id
                if not user:
                    continue  # Skip if user is missing

                sub_dict = {
                    'sub_id': sub.sub_id,
                    'warn_days': sub.warn_days,
                    'stop_days': sub.stop_days,
                    'price': str(sub.price),
                    'discount': str(sub.discount),
                    'Active_date': sub.Active_date,
                    'deactive': sub.deactive,
                    'status': sub.status,
                    'user_id': user.user_id,
                    'email': user.email,
                    'contact': user.contact,
                    'firstname': user.firstname,
                    'lastname': user.lastname
                }
                subscription_data.append(sub_dict)

            return JsonResponse(subscription_data, safe=False)

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)

 


    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Extract values
            user_id = data.get('user_id')
            warn_days = data.get('warn_days', 30)  # Expecting int
            stop_days = data.get('stop_days', 30)
            price = data.get('price', 0)
            discount = data.get('discount', 0)


            warn_days = int(warn_days)
            stop_days = int(stop_days) if stop_days is not None else 0
            if not all([user_id]):
                return JsonResponse({'error': 'user_id, are required.'}, status=400)

            try:
                user_instance = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User with the given user_id does not exist.'}, status=404)


            active_date = timezone.now()
            warn_date = (active_date + timedelta(days=int(warn_days))).date()
            stop_date = (warn_date + timedelta(days=int(stop_days)))
    
            # Create or update Subscription
            subscription, created = Subscription.objects.update_or_create(
                user_id=user_instance,
                defaults={
                    'warn_days': warn_days,
                    'stop_days': stop_days,
                    'price': price,
                    'discount': discount,
                    'Active_date': active_date,
                }
            )

            # Create Invoice
            invoice = InvoiceTable(
                subscription=subscription,
                start_date=active_date,  # Now never null
                end_date=warn_date
            )
            invoice.save()

                    # Only create invoice if subscription is active
            if subscription.status == "Active":
                invoice = InvoiceTable.objects.create(
                    subscription=subscription,
                    start_date=active_date,
                    end_date=warn_date
                )
                invoice.save()


            return JsonResponse({
                'sub_id': subscription.sub_id,
                'user_id': subscription.user_id.user_id,
                'warn_date': subscription.warn_days,
                'stop_date': subscription.stop_days,
                'price': float(subscription.price),
                'discount': float(subscription.discount),
                'inv_id': invoice.inv_id,
                'message': 'Subscription and invoice created successfully.'
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid HTTP method.'}, status=405)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_single_highchart_data(request):
    if request.method == "GET":
        try:
            # Get query parameters
            gateway_name = request.GET.get("gateway")
            value_name = request.GET.get("value_name")
            from_date = request.GET.get("from_date")
            if not gateway_name or not value_name:
                return JsonResponse({"error": "Gateway name and value name are required"}, status=400)
            # Convert the date string to a timezone-aware datetime object
            if from_date:
                from_date = timezone.make_aware(
                    datetime.strptime(from_date, "%Y-%m-%d"), timezone.get_current_timezone()
                )
            # Fetch the gateway
            try:
                gateway = Gateways.objects.get(gateway_name=gateway_name)
            except Gateways.DoesNotExist:
                return JsonResponse({"error": "Gateway not found"}, status=404)
            # Fetch analyzers for the gateway
            analyzers = Analyzer.objects.filter(gateway=gateway)
            if not analyzers.exists():
                return JsonResponse({"error": "No analyzers found for the gateway"}, status=404)
            # Prepare Highcharts data
            highchart_data = []
            for port_name in ["COM_1", "COM_2", "e1", "e2"]:
                port_analyzers = analyzers.filter(port=port_name)
                port_data = {
                    "name": port_name,
                    "data": []
                }
                for analyzer in port_analyzers:
                    metadata_entries = MetaData.objects.filter(analyzer=analyzer)
                    if from_date:
                        metadata_entries = metadata_entries.filter(timestamp__gte=from_date)
                    value_series = []
                    for metadata in metadata_entries:
                        for i in range(1, 21):
                            name = getattr(metadata, f"value{i}_name", None)
                            value = getattr(metadata, f"value{i}_value", None)
                            if name == value_name:
                                timestamp_str = metadata.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                                value_series.append([timestamp_str, value])
                    # Sort analyzer data
                    value_series.sort(key=lambda x: x[0])
                    if value_series:
                        port_data["data"].append({
                            "name": analyzer.name,
                            "data": value_series
                        })
                # Sort analyzers by earliest timestamp
                port_data["data"].sort(key=lambda x: x["data"][0][0] if x["data"] else float("inf"))
                if port_data["data"]:
                    highchart_data.append(port_data)
            return JsonResponse({
                "gateway": gateway_name,
                "value_name": value_name,
                "ports": highchart_data
            }, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)


# views.py
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_user(request, users_id):
    if request.method == 'POST':
        try:
            # Parse request data
            data = json.loads(request.body)
            print('user Creation', data)

            # Extract fields from request data
            firstname = data.get('firstname')
            lastname = data.get('lastname')
            email = data.get('email')
            password = data.get('password')
            contact = data.get('contact')
            role = data.get('role', 'user')
            is_online = data.get('is_online', False)
            adress = data.get('adress')
            zip_code = data.get('zip_code')
            image_base64 = data.get('image')

            if not all([firstname, lastname, email, contact, password, ]):
                return JsonResponse({'error': 'All required fields must be provided.'}, status=400)

            if role not in dict(User.ROLES):
                return JsonResponse({'error': 'Invalid role.'}, status=400)

            # Create user object
            user = User(
                firstname=firstname,
                lastname=lastname,
                email=email,
                contact=contact,
                password=password,
                role=role,
                adress=adress,
                zip_code=zip_code,
                image=image_base64,
                is_online=is_online,
                created_by_id = data.get('created_by_id')
  # Setting the current admin as the creator
            )
            user.save()

            # Assign hardware if provided
            hardware_ids = data.get('hardware', [])
            if hardware_ids:
                hardware_list = Hardware.objects.filter(hardware_id__in=hardware_ids)
                if hardware_list.exists():
                    user.hardware.add(*hardware_list)
                else:
                    return JsonResponse({'error': 'No valid hardware found.'}, status=404)

            # Create Invoice and other operations...
            admincr_obj = admincr(cr_id=user.user_id, admin_id=users_id)
            admincr_obj.save()

            return JsonResponse({
                'id': user.user_id,
                'firstname': user.firstname,
                'lastname': user.lastname,
                'email': user.email,
                'contact': user.contact,
                'role': user.role,
                'adress': user.adress,
                'zip_code': user.zip_code,
                'unique_key': user.unique_key,
                'is_online': user.is_online,
                'message': 'User created successfully.',
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid HTTP method.'}, status=405)

#for login user
# @csrf_exempt
# def login_user(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             email = data.get('email')
#             password = data.get('password')
            
#             try:
#                 user = User.objects.get(email=email)
                
#                 if user.password == password:
#                     user.is_online = True
#                     user.save()
#                     refresh = RefreshToken.for_user(user)
#                     access_token = str(refresh.access_token)
#                     refresh_token = str(refresh)
                    
#                     return JsonResponse({
#                         'success': True,
#                         'message': 'Login successful',
#                         'user_id': user.user_id,
#                         'firstname': user.firstname,
#                         'lastname': user.lastname,
#                         'role': user.role,
#                         'image': user.image,
#                         'unique_key' : str(user.unique_key),
#                         'access': access_token,
#                         'refresh': refresh_token,
#                         'is_online' : user.is_online
#                     }, status=200)
                    
#                 else:
#                     return JsonResponse({'success': False, 'message': 'Invalid username or password'}, status=401)
            
#             except User.DoesNotExist:
#                 return JsonResponse({'success': False, 'message': 'User Not Found'}, status=404)
        
#         except json.JSONDecodeError:
#             return JsonResponse({'success': False, 'message': 'Invalid data'}, status=400)
    
#     return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)


#for login user
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            try:
                user = User.objects.get(email=email)
                
                if user.password == password:
                    user.is_online = True
                    user.save()
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    refresh_token = str(refresh)
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Login successful',
                        'user_id': user.user_id,
                        'firstname': user.firstname,
                        'lastname': user.lastname,
                        'role': user.role,
                        'image': user.image,
                        'unique_key' : str(user.unique_key),
                        'access': access_token,
                        'refresh': refresh_token,
                        'is_online' : user.is_online
                    }, status=200)
                    
                else:
                    return JsonResponse({'success': False, 'message': 'Invalid username or password'}, status=401)
            
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'User Not Found'}, status=404)
        
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid data'}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_user_gateways(request):
    user_id = request.GET.get('user_id')

    if not user_id:
        return JsonResponse({'success': False, 'message': 'User ID is required'}, status=400)

    try:
        print(f"🔍 Fetching gateway details for user_id: {user_id}")

        # ✅ Use filter to get all gateways for the user
        gateways = Gateways.objects.filter(user_id=user_id)


        # ✅ Prepare the list of gateways
        gateway_list = []
        for g in gateways:
            gateway_list.append({
                "G_id": g.G_id,
                "gateway_name": g.gateway_name,
                "mac_address": g.mac_address,
                "status": g.status,
                "deploy_status": g.deploy_status,
                "config": g.config,
      
                "analyzers_by_port": g.analyzers_by_port,
                "created_by_id": g.created_by_id,
            })

        # ✅ Return both count and list
        return JsonResponse({
            "success": True,
  
            "gateways": gateway_list
        }, status=200)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)


#for logout*******
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def logout_user(request):
    if request.method=='POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            try:
                user = User.objects.get(email=email)
                user.is_online=False
                user.save()
                
                return JsonResponse({
                    'success' : True,
                    'message' : 'Logout successfully'
                }, status=200)
            except User.DoesNotExist:
                return JsonResponse({'message' : 'User not found'})
        except json.JSONDecodeError:
            return JsonResponse({'message' : False, 'message' : 'invalid data'}, status=400)
    return JsonResponse({'success':False, 'message':'invalid method'})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def selected_analyzer_data(request):
    try:
        analyzer_id = request.GET.get("analyzer_id")
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")

        if not analyzer_id or not start_date_str or not end_date_str:
            return JsonResponse({"error": "analyzer_id, start_date, and end_date are required."}, status=400)

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "Date format must be YYYY-MM-DD."}, status=400)

        if start_date > end_date:
            return JsonResponse({"error": "start_date must be earlier than or equal to end_date."}, status=400)

        try:
            analyzer = Analyzer.objects.get(analyzer_id=analyzer_id)
        except Analyzer.DoesNotExist:
            return JsonResponse({"error": "Analyzer not found"}, status=404)

        # Filter metadata using aware datetime range
        start_datetime = make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = make_aware(datetime.combine(end_date, datetime.max.time()))

        metadata_qs = MetaData.objects.filter(
            analyzer=analyzer,
            created_at__range=(start_datetime, end_datetime)
        ).order_by('date')

        if not metadata_qs.exists():
            return JsonResponse({"error": "No metadata found for this analyzer in the selected date range"}, status=404)

        first_date = metadata_qs.first().date
        last_date = metadata_qs.last().date

        metadata_list = []
        for meta in metadata_qs:
            values = {}
            for i in range(1, 21):
                name = getattr(meta, f"value{i}_name", None)
                value = getattr(meta, f"value{i}_value", None)
                if name:
                    values[name] = value

            metadata_list.append({
                "timestamp": meta.date,
                "mac_address": meta.mac_address,
                "values": values
            })

        return JsonResponse({
            "analyzer_id": analyzer_id,
            "first_date": first_date,
            "last_date": last_date,
            "metadata": metadata_list
        }, status=200, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

#inserting project values to database
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_project(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Check required fields including 'name'
            required_fields = [
                'user_id', 'total_power', 'kw', 'kva', 
                'power_factor', 'frequency', 'current_l1', 'current_l2', 
                'current_l3', 'volt_l1', 'volt_l2', 'volt_l3', 
                'power_l1', 'power_l2', 'power_l3'
            ]
            
            for field in required_fields:
                if field not in data:
                    return JsonResponse({'error': f'Missing field: {field}'}, status=400)
            
            user = User.objects.get(pk=data['user_id'])
            
            project = Project.objects.create(
                user_id=user,
                total_power=data['total_power'],
                kw=data['kw'],
                kva=data['kva'],
                power_factor=data['power_factor'],
                frequency=data['frequency'],
                current_l1=data['current_l1'],
                current_l2=data['current_l2'],
                current_l3=data['current_l3'],
                volt_l1=data['volt_l1'],
                volt_l2=data['volt_l2'],
                volt_l3=data['volt_l3'],
                power_l1=data['power_l1'],
                power_l2=data['power_l2'],
                power_l3=data['power_l3']
            )
            return JsonResponse({'message': 'Project created successfully', 'project_id': project.project_id}, status=200)
        except KeyError as e:
            return JsonResponse({'error': f'Missing field: {str(e)}'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=400)
        except Hardware.DoesNotExist:
            return JsonResponse({'error': 'Hardware not found'}, status=400)
        except IntegrityError as e:
            return JsonResponse({'error': f'Integrity error: {str(e)}'}, status=400)
        except ValidationError as e:
            return JsonResponse({'error': f'Validation error: {str(e)}'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def latest_project_data(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')

        if not user_id:
            return JsonResponse({'error': 'User ID is required'}, status=400)

        try:
            # Retrieve all projects for the user, ordered by last_updated (ascending for consistency)
            projects = Project.objects.filter(user_id=user_id).order_by('last_updated')

            if not projects.exists():
                return JsonResponse({'error': 'No projects found for this user'}, status=404)

            # Initialize data structures
            current_data = {'L1': [], 'L2': [], 'L3': []}
            voltage_data = {'L1': [], 'L2': [], 'L3': []}
            power_data = {'L1': [], 'L2': [], 'L3': []}

            if from_date and to_date:
                try:
                    from_date = timezone.make_aware(datetime.strptime(from_date, '%Y-%m-%d'))
                    to_date = timezone.make_aware(datetime.strptime(to_date, '%Y-%m-%d')).replace(hour=23, minute=59, second=59)
                    projects = projects.filter(last_updated__range=(from_date, to_date))

                    if not projects.exists():
                        return JsonResponse({'message': 'No data available for the selected date range.'}, status=404)

                except ValueError:
                    return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD format for from_date and to_date.'}, status=400)

            # Process each project
            for project in projects:
                try:
                    time_ms = int(project.last_updated.timestamp() * 1000)  # Convert to ms

                    current_data['L1'].append([time_ms, float(project.current_l1)])
                    current_data['L2'].append([time_ms, float(project.current_l2)])
                    current_data['L3'].append([time_ms, float(project.current_l3)])

                    voltage_data['L1'].append([time_ms, float(project.volt_l1)])
                    voltage_data['L2'].append([time_ms, float(project.volt_l2)])
                    voltage_data['L3'].append([time_ms, float(project.volt_l3)])

                    power_data['L1'].append([time_ms, float(project.power_l1)])
                    power_data['L2'].append([time_ms, float(project.power_l2)])
                    power_data['L3'].append([time_ms, float(project.power_l3)])

                except Exception as e:
                    logging.error(f'Error processing project data: {str(e)}')
                    return JsonResponse({'error': 'Error processing project data.'}, status=500)

            # Structure response data
            response_data = {
                'current': [{'name': label, 'data': data} for label, data in current_data.items()],
                'voltage': [{'name': label, 'data': data} for label, data in voltage_data.items()],
                'power': [{'name': label, 'data': data} for label, data in power_data.items()],
            }

            return JsonResponse(response_data)

        except Exception as e:
            logging.error(f'Server error: {str(e)}')
            return JsonResponse({'error': 'Server error occurred.'}, status=500)


#getting whole user data
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def get_user_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            
            if not user_id:
                return JsonResponse({'error': 'User ID is required.'}, status=400)
            
            try:
                user_data = Project.objects.get(user_id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'No data found for this user.'}, status=404)
            
            response_data = {
                'user_id': user_id,
                'total_power': user_data.total_power,
                'kw': user_data.kw,
                'kva': user_data.kva,
                'power_factor': user_data.power_factor,
                'frequency': user_data.frequency,
                'current_l1': user_data.current_l1,
                'current_l2': user_data.current_l2,
                'current_l3': user_data.current_l3,
                'volt_l1': user_data.volt_l1,
                'volt_l2': user_data.volt_l2,
                'volt_l3': user_data.volt_l3,
                'power_l1': user_data.power_l1,
                'power_l2': user_data.power_l2,
                'power_l3': user_data.power_l3,
            }
            
            return JsonResponse(response_data, status=200)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid HTTP method.'}, status=405)

#getting total number of users
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def total_uers(request):
    if request.method == 'GET':
        try:
            # Count only users with role='user'
            user_count = User.objects.filter(role='user').count()
            return JsonResponse({'total_users': user_count}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'invalid method'}, status=405)


#getting frequency and power factor
logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_latest_project_data(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')

        if not user_id:
            return JsonResponse({'error': 'User ID is required'}, status=400)

        try:
            latest_project = Project.objects.filter(user_id=user_id).order_by('-last_updated').first()

            if not latest_project:
                return JsonResponse({'error': 'No projects found for this user'}, status=404)

            response_data = {
                'frequency': latest_project.frequency,
                'power_factor': latest_project.power_factor,
                'last_updated': latest_project.last_updated,
            }
            
            # Logging for debugging
            logger.info(f"Latest project data for user {user_id}: {response_data}")

            return JsonResponse(response_data, status=200)

        except Project.DoesNotExist:
            return JsonResponse({'error': 'Project not found'}, status=404)
        except Exception as e:
            logger.error(f"Error fetching latest project data: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=405)




#adding hardware to database
@api_view(['POST'])
@permission_classes([permissions.AllowAny]) 
def add_hardware(request):
    if request.method == 'POST':
        try:
            # Parse the JSON body
            data = json.loads(request.body)
        
            project_id = data.get('project_id')
            name = data.get('name')
            serial_number = data.get('serial_number') 
            is_connected = data.get('is_connected', False)  
            
            try:
                project = Project.objects.get(project_id=project_id)
            except Project.DoesNotExist:
                return JsonResponse({"error": "Project not found."}, status=404)
            
            hardware = Hardware.objects.create(
                project_id=project,
                name=name,
                serial_number=serial_number,
                is_connected=is_connected
            )
            
            return JsonResponse({"message": "Hardware added successfully!", "hardware_id": hardware.hardware_id}, status=201)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request method."}, status=405)




#getting total number of hardware......
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def hardware_count(request , project_id):
    if request.method == 'GET':
        try:
            project = Project.objects.get(project_id=project_id)
        except Project.DoesNotExist:
            return JsonResponse({'Error' : 'Project not found'}, status = 404 )
        
        total_hardware = Hardware.objects.filter(project_id=project).count()
        return JsonResponse({'project_id' : project_id , 'hardware_count' : total_hardware})
    return JsonResponse({'Error' : 'invalid method'}, status = 400)
            

#getting connected hardware count
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def connected_hardware_count(request , project_id):
    if request.method == 'GET':
        try:
            project = Project.objects.get(project_id=project_id)
        except Project.DoesNotExist:
            return JsonResponse({'Error' : 'Project not exist'}, status = 404)
        
        count = Hardware.objects.filter(project_id=project , is_connected=True).count()
        return JsonResponse({'project_id' : project_id , 'count' : count})
    return JsonResponse({'error' : 'invalid request'}, status = 400)
        

#user_project related table view
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_project(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            project_id = data.get('project_id')
            
            try:
                user = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'Error' : 'User not found'}, status =404)
            
            try:
                project = Project.objects.get(project_id=project_id)
            except Project.DoesNotExist:
                return JsonResponse({'Error' : 'Project not found'}, status = 404)
            
            user_project = User_Project.objects.create(user_id=user , project_id=project)
            return JsonResponse({
                'up_id' : user_project.up_id,
                'user_id' : user_project.user_id.user_id,
                'project_id' : user_project.project_id.project_id
            },status=201)
        except json.JSONDecodeError:
            return JsonResponse({'Error' : 'Invalid json'})
    return JsonResponse({'Error' : 'Invvalid method'},status  = 400)

#getting the whole user
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetching_users(request):
    user_id = request.GET.get('user_id')  # get user_id from query param

    if user_id:
        users = User.objects.filter(user_id=user_id).values(
            'user_id', 'firstname', 'lastname', 'email', 'contact',
            'role', 'adress', 'zip_code', 'is_online', 'image', 'password', 'created_by_id'
        )
    else:
        users = User.objects.all().values(
            'user_id', 'firstname', 'lastname', 'email', 'contact',
            'role', 'adress', 'zip_code', 'is_online', 'image', 'password', 'created_by_id'
        )

    user_list = list(users)
    return JsonResponse(user_list, safe=False)


#for deleting user
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def delete_user(request , user_id):
    if request.method == 'POST':
        try:
            user = get_object_or_404(User , user_id = user_id)
            print("users_id from URL parameter:", user_id)
            user.delete()
            return JsonResponse({'message' : 'User Deleted Successfully'}, status=200)
            
        except Exception as e :
            return JsonResponse({'error' : str(e)}, status= 500)
    return JsonResponse({'error' : 'invalid request method'}, status = 405)
            

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_admin_users(request):
    admins = User.objects.filter(role='admin').values('user_id', 'firstname', 'lastname', 'email')
    return JsonResponse({'admins': list(admins)}, safe=False)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def update_user(request, user_id):
    try:
        data = json.loads(request.body)
        user = get_object_or_404(User, user_id=user_id)

        user.firstname = data.get('firstname', user.firstname)
        user.lastname = data.get('lastname', user.lastname)
        user.email = data.get('email', user.email)
        user.contact = data.get('contact', user.contact)
        user.role = data.get('role', user.role)
        user.adress = data.get('adress', user.adress)
        user.zip_code = data.get('zip_code', user.zip_code)
        user.password = data.get('password', user.password)
        user.image = data.get('image', user.image)

        # ✅ Fix here: get 'created_by_id' from frontend payload
        created_by_id = data.get('created_by_id')
        if created_by_id:
            admin_user = User.objects.filter(user_id=created_by_id, role='admin').first()
            if admin_user:
                user.created_by = admin_user

        user.save()

        return JsonResponse({'message': 'User updated successfully', 'user_id': user.user_id}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

#for fetching hardware

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_Hardware(request, user_id):
    if request.method == 'GET':
        try:
            projects = Project.objects.filter(user_id=user_id)
            hardware = Hardware.objects.filter(project_id__in=projects).values(
                "hardware_id", "name", "serial_number", "is_connected"
            )
            hardware_list = list(hardware)
            return JsonResponse(hardware_list, safe=False)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)


#update hardware 
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def update_hardware(request , hardware_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            hardware = get_object_or_404(Hardware , hardware_id=hardware_id)
            
            hardware.name = data.get('name' , hardware.name)
            hardware.serial_number = data.get('serial_number', hardware.serial_number)
            hardware.is_connected = data.get('is_connected', hardware.is_connected)
            
            hardware.save()
            return JsonResponse({'message' : 'user updated successfully'},status=200)
        except Exception as e:
            return JsonResponse({'error':str(e)}, status=500)
    else:
        return JsonResponse({'error' : 'invalid Http method'}, status=405)
    
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def delete_hardware(request , hardware_id):
    if request.method == 'POST':
        try:
            # Find the gateway using its primary key (G_id)
            gateway = get_object_or_404(Gateways, G_id=hardware_id)
            gateway.delete()
            return JsonResponse({'message': 'Gateway deleted successfully'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid HTTP method'}, status=405)
    
    
#multiple user delete API
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def delete_selected_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])
            
        User.objects.filter(user_id__in=user_ids).delete()
            
        return JsonResponse({'message' : 'users deleted Successfully'}, status=200)
    return JsonResponse({'message' : 'invalid request methood'}, status=405)

#multiple hardware delete API
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def delete_selected_hardware(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        hardware_ids = data.get('hardware_ids',[])
        
        Hardware.objects.filter(hardware_id__in=hardware_ids).delete()
        
        return JsonResponse({'message' : 'Hardware deleted successfully'}, status=200)
    return JsonResponse({'error' : 'invalid request method'}, status=405)


#create Project Manager
from django.db import transaction

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def Create_Project_Manager(request):
    if request.method == 'POST':
        try:
            # Parse incoming JSON data
            data = json.loads(request.body)
        
            # Extract fields from the incoming data
            user_id = data.get('user_id')
            name = data.get('name')
            longitude = data.get('longitude')
            latitude = data.get('latitude')
            address = data.get('address')
            gateway_ids = data.get('gateway_ids', [])  # Get the list of gateway IDs (if any)
            
            # Check for missing fields
            if not all([user_id, name, longitude, latitude, address]):
                return JsonResponse({'error': 'Missing required fields: user_id, name, longitude, latitude, address'}, status=400)
        
            # Check if user exists
            try:
                user = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User does not exist'}, status=404)
            
            # Use atomic transaction to ensure data integrity
            with transaction.atomic():
                # Create the Project Manager entry
                PM = Project_Manager.objects.create(
                    user_id=user,
                    name=name,
                    longitude=longitude,
                    latitude=latitude,
                    address=address,
                    is_active=False  # Initially setting the project as inactive
                )
                
                # If gateway_ids are provided, assign gateways to the project
                if gateway_ids:
                    gateways = Gateways.objects.filter(G_id__in=gateway_ids)
                    
                    # Check if the gateways exist and are not already assigned
                    if gateways.count() != len(gateway_ids):
                        return JsonResponse({'error': 'Some gateways are invalid or already assigned'}, status=400)
                    
                    # Assign the gateways to the project
                    for gateway in gateways:
                        if gateway.project is not None:
                            return JsonResponse({'error': f'Gateway {gateway.G_id} is already assigned to another project.'}, status=400)
                        gateway.project = PM  # Assuming the Gateway model has a ForeignKey to Project_Manager
                        gateway.save()

            # Return success response with the ID of the newly created Project Manager
            return JsonResponse({
                'message': 'Project created successfully',
                'ID': PM.PM_id,
                'User': user_id,
                'Assigned Gateways': gateway_ids
            }, status=201)
        
        except Exception as e:
            # Log the exception for debugging
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method. Only POST is allowed.'}, status=405)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def Get_Project_Manager(request, user_id):     
    if request.method == 'GET':
        try:
            project_managers = Project_Manager.objects.filter(user_id=user_id)
            
            if not project_managers.exists():
                return JsonResponse({'error': 'Project Manager not found'}, status=404)
            
            response_data = []
            for project_manager in project_managers:
                connected_gateways = project_manager.gateways.all()

                gateways_data = []
                for gateway in connected_gateways:
                    # Fetch analyzers connected to this gateway
                    analyzers = Analyzer.objects.filter(gateway=gateway)
                    analyzers_data = [
                        {
                            'analyzer_id': analyzer.analyzer_id,
                            'name': analyzer.name
                        }
                        for analyzer in analyzers
                    ]

                    gateways_data.append({
                        'G_id': gateway.G_id,
                        'gateway_name': gateway.gateway_name,
                        'mac_address': gateway.mac_address,
                        'status': gateway.status,
                        'deploy_status': gateway.deploy_status,
                        'config': gateway.config,
                        'analyzers': analyzers_data  # Include analyzers under each gateway
                    })
                
                response_data.append({
                    'PM_id': project_manager.PM_id,
                    'user_id': project_manager.user_id.user_id,
                    'name': project_manager.name,
                    'longitude': str(project_manager.longitude),
                    'latitude': str(project_manager.latitude),
                    'address': project_manager.address,
                    'is_active': project_manager.is_active,
                    'connected_gateways': gateways_data
                })
            
            return JsonResponse({
                'message': 'Project Managers retrieved successfully',
                'project_managers': response_data
            }, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'message': 'Invalid request method'}, status=405)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def edit_project_manager(request, pm_id):

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

        # Fetch project manager by PM_id
            try:
                project_manager = Project_Manager.objects.get(PM_id=pm_id)
            except Project_Manager.DoesNotExist:
                return JsonResponse({'error': 'Project Manager not found'}, status=404)

        # Update fields
            project_manager.name = data.get('name', project_manager.name)
            project_manager.longitude = data.get('longitude', project_manager.longitude)
            project_manager.latitude = data.get('latitude', project_manager.latitude)
            project_manager.address = data.get('address', project_manager.address)

            project_manager.save()

            return JsonResponse({
                'message': 'Project Manager updated successfully',
                'PM_id': project_manager.PM_id,
                'name': project_manager.name,
                'longitude': str(project_manager.longitude),
                'latitude': str(project_manager.latitude),
                'address': project_manager.address,
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'message': 'Invalid request method'}, status=405)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def Get_User_Project_Count(request, user_id):
    if request.method == 'GET':
        try:
            project_count = Project_Manager.objects.filter(user_id=user_id).count()

            return JsonResponse({
                'user_id': user_id,
                'project_count': project_count
            }, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'message': 'Invalid request method'}, status=405)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def Get_All_Projects(request):
    if request.method == 'GET':
        try:
            # Retrieve all Project_Manager entries
            project_managers = Project_Manager.objects.all()
            
            if not project_managers.exists():
                return JsonResponse({'error': 'No projects found'}, status=404)
            
            # Prepare the response data
            response_data = []
            for project_manager in project_managers:
                # Fetch connected gateways using the related_name 'gateways'
                connected_gateways = project_manager.gateways.all()
                
                # Prepare the gateway data
                gateways_data = [
                    {
                        'G_id': gateway.G_id,
                        'gateway_name': gateway.gateway_name,
                        'mac_address': gateway.mac_address,
                        'status': gateway.status,
                        'deploy_status': gateway.deploy_status,
                        'config': gateway.config,
                        # 'j_object': gateway.j_object,
                    }
                    for gateway in connected_gateways
                ]
                
                # Append the project manager data to the response
                response_data.append({
                    'PM_id': project_manager.PM_id,
                    'user_id': project_manager.user_id.user_id if project_manager.user_id else None,
                    'user_firstname': project_manager.user_id.firstname if project_manager.user_id else None,
                    'user_lastname': project_manager.user_id.lastname if project_manager.user_id else None,
                    'created_by_id': project_manager.user_id.created_by.user_id if project_manager.user_id and project_manager.user_id.created_by else None,

                    'user_image': project_manager.user_id.image if project_manager.user_id else None,
                    'name': project_manager.name,
                    'longitude': str(project_manager.longitude),
                    'latitude': str(project_manager.latitude),
                    'address': project_manager.address,
                    'is_active': project_manager.is_active,
                    'connected_gateways': gateways_data  # Include connected gateways here
                })
            
            return JsonResponse({
                'message': 'All projects retrieved successfully',
                'projects': response_data
            }, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'message': 'Invalid request method'}, status=405)



@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def Get_superAdmin_Project_Count(request):
    if request.method == 'GET':
        try:
            # Count all projects
            total_projects = Project_Manager.objects.count()
            return JsonResponse({
                'total_projects': total_projects
            }, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'message': 'Invalid request method'}, status=405)

# create gateway by project manager
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_Gateways(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print('data:', data)

            gateway_name = data.get('gateway_name')
            mac_address = data.get('mac_address')
            status = data.get('status', False)
            deploy_status = data.get('deploy_status', 'warehouse')
            config = data.get('config', False)
            created_by_id = data.get('created_by_id')  # ✅ Get from request

            analyzers_by_port = {
                'com1': [],
                'com2': [],
                'e1': [],
                'e2': []
            }

            gateway = Gateways.objects.create(
                gateway_name=gateway_name,
                mac_address=mac_address,
                status=status,
                deploy_status=deploy_status,
                config=config,
                analyzers_by_port=analyzers_by_port,
                user_id=None,
                created_by_id=created_by_id  # ✅ Important!
            )

            return JsonResponse({
                'message': 'Gateway created successfully',
                "Gateway Id": gateway.G_id,
                "analyzers_by_port": analyzers_by_port,
                "created_by_id": created_by_id,
            }, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=405)

# update gateway ///////////////////////


# count total gateways****************************
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_total_gateways(request):
    if request.method=="GET":
        try:
            total_gateways_count = Gateways.objects.count()
            
            return JsonResponse({
                "message" : "Gateways retrives Successfully",
                "gateways_count" : total_gateways_count
            },status=200)
        except Exception as e:
            return JsonResponse({
                "error" : str(e)
            },status=400)

# count deployed gateways******************
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_deployed_gateways(request):
    if request.method=="GET":
        try:
            deployed_gateways_count = Gateways.objects.filter(deploy_status = 'deployed').count()
            
            return JsonResponse({
                "message" : "Deployed Gateways retrives Successfully",
                "deployed_gateways_count" : deployed_gateways_count
            },status=200)
        except Exception as e:
            return JsonResponse({
                "error" : str(e)
            },status=400)
            
            
# count user aloted gateways
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_user_aloted_gateways(request):
    if request.method == 'GET':
        try:
            user_aloted = Gateways.objects.filter(deploy_status = 'user_aloted').count()
            
            return JsonResponse({
                'message' :'User aloted Gateways',
                'user_aloted_count' : user_aloted 
            }, status=200)
        except Exception as e:
            return JsonResponse({
                "error" : str(e)
            }, status=400)


# fetch those gateway available in warehouse
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_unassigned_gateways(request):
    if request.method == "GET":
        try:
            # Fetch only unassigned gateways where user_id is null
            unassigned_gateways = Gateways.objects.filter(user_id__isnull=True)

            # Debugging: Check if any unassigned gateways are fetched
            print(f"Unassigned Gateways found: {unassigned_gateways.count()}")

            if not unassigned_gateways.exists():
                return JsonResponse({'message': 'No unassigned gateways found'}, status=404)

            # Construct the response data
            unassigned_gateways_data = [
                {
                    'G_id': gateway.G_id,
                    'gateway_name': gateway.gateway_name,
                    'mac_address': gateway.mac_address,
                    'status': gateway.status,
                    'deploy_status': gateway.deploy_status,
                    'config': gateway.config,
                    'created_by_id': gateway.created_by_id
                    
                }
                for gateway in unassigned_gateways
            ]

            return JsonResponse({'UnassignedGateways': unassigned_gateways_data}, status=200)
        
        except Exception as e:
            print(f"Error occurred: {str(e)}")  # Debugging: Print the error
            return JsonResponse({'error': str(e)}, status=400)

    print(f"Invalid request method: {request.method}")  # Debugging: Check the request method
    return JsonResponse({'message': 'Invalid request method'}, status=405)


# APi to assign gateway to a user
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def assign_gateways_to_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            gateway_ids = data.get('gateway_ids')
            print('data:', data)

            if not user_id or not gateway_ids:
                return JsonResponse({'message': 'User ID and Gateway IDs are required'}, status=400)

            user = User.objects.filter(user_id=user_id).first()
            if not user:
                return JsonResponse({'message': 'User not found'}, status=404)

            # Fetch the gateways that are not assigned to any user and have IDs in the gateway_ids list
            gateways = Gateways.objects.filter(G_id__in=gateway_ids, user_id__isnull=True)

            if gateways.count() != len(gateway_ids):
                return JsonResponse({'message': 'Some gateways are already assigned to users'}, status=400)

            # Update the deploy_status and assign them to the user
            gateways.update(user_id=user_id, deploy_status='user_aloted')

            return JsonResponse({'message': 'Gateways assigned successfully'}, status=200)

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=405)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_gateways_of_user(request):
    if request.method == "GET":
        try:
            # Get user_id from query parameters
            user_id = request.GET.get('user_id')

            # Validate that user_id is provided
            if not user_id:
                return JsonResponse({'message': 'User ID is required'}, status=400)

            # Check if the user exists
            user = User.objects.filter(user_id=user_id).first()
            if not user:
                return JsonResponse({'message': 'User not found'}, status=404)

            # Fetch all gateways assigned to the user
            gateways = Gateways.objects.filter(user_id=user_id)

            # Construct the response data
            gateways_data = []
            for gateway in gateways:
                # Add analyzers_by_port if analyzers exist
                analyzers_by_port = {
                    'com1': list(Analyzer.objects.filter(gateway=gateway, port='com1').values()) if 'Analyzer' in locals() else [],
                    'com2': list(Analyzer.objects.filter(gateway=gateway, port='com2').values()) if 'Analyzer' in locals() else [],
                    'e1': list(Analyzer.objects.filter(gateway=gateway, port='e1').values()) if 'Analyzer' in locals() else [],
                    'e2': list(Analyzer.objects.filter(gateway=gateway, port='e2').values()) if 'Analyzer' in locals() else [],
                }

                # Add the gateway data
                gateway_data = {
                    'G_id': gateway.G_id,
                    'gateway_name': gateway.gateway_name,
                    'mac_address': gateway.mac_address,
                    'status': gateway.status,
                    'deploy_status': gateway.deploy_status,
                    'config': gateway.config,
                    'analyzers_by_port': analyzers_by_port
                }
                gateways_data.append(gateway_data)

            # Return the gateways data
            return JsonResponse({'Gateways': gateways_data}, status=200)

        except Exception as e:
            print(f"Error occurred: {str(e)}")  # Debugging
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=405)

@api_view(['PUT'])
@permission_classes([permissions.AllowAny])
def update_gateway(request):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            gateway_id = data.get('G_id')
            project_id = data.get('project_id')  # Ensure project_id is passed
            deploy_status = data.get('deploy_status')

            if not gateway_id or not project_id:
                return JsonResponse({'message': 'Gateway ID and Project ID are required'}, status=400)

            # Fetch gateway
            gateway = Gateways.objects.filter(G_id=gateway_id).first()
            if not gateway:
                return JsonResponse({'message': 'Gateway not found'}, status=404)

            # Update fields
            gateway.project_id = project_id
            gateway.deploy_status = deploy_status
            gateway.save()
            
            project = Project_Manager.objects.filter(PM_id = project_id).first()
            if project:
                has_deployed_gateway = Gateways.objects.filter(project_id=project_id,deploy_status="deployed").exists()
                project.is_active = has_deployed_gateway
                project.save()

            return JsonResponse({'message': 'Gateway and project updated successfully'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'message': 'Invalid request method'}, status=405)



@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_deployed_gateways_of_user(request):
    if request.method == "GET":
        try:
            # Get project_id from query parameters
            project_id = request.GET.get('project_id')
            if not project_id:
                return JsonResponse({'message': 'Project ID is required'}, status=400)

            # Debug: Log the incoming project_id
            print(f"Fetching deployed gateways for Project ID: {project_id}")

            # Fetch gateways
            deployed_gateways = Gateways.objects.filter(deploy_status='deployed', project_id=project_id)

            if not deployed_gateways.exists():
                print(f"No gateways found for Project ID: {project_id}")
                return JsonResponse({'message': 'No deployed gateways found for the project'}, status=404)

            # Prepare response data
            gateways_data = [
                {
                    'G_id': gateway.G_id,
                    'gateway_name': gateway.gateway_name,
                    'mac_address': gateway.mac_address,
                    'status': gateway.status,
                    'deploy_status': gateway.deploy_status,
                    'config': gateway.config,
                    'project_id': gateway.project_id,
                }
                for gateway in deployed_gateways
            ]

            # Debug: Confirm the number of gateways found
            print(f"Found {len(gateways_data)} gateways for Project ID: {project_id}")

            return JsonResponse({'deployed_gateways': gateways_data}, status=200)

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=405)


# fetch user gateways in dropdown admin
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_gateways_of_usersList(request):
    if request.method == "GET":
        try:
            user_id = request.GET.get('user_id')  # Get user_id from the query parameters
            print('user_id:', user_id)

            if not user_id:
                return JsonResponse({'message': 'User ID is required'}, status=400)

            user = User.objects.filter(user_id=user_id).first()
            if not user:
                return JsonResponse({'message': 'User not found'}, status=404)

            # Fetch the gateways that are assigned to this user
            gateways = Gateways.objects.filter(user_id=user_id)

            # Prepare the data to return
            gateways_data = []
            for gateway in gateways:
                # Fetch analyzers grouped by their ports
                analyzers_by_port = {
                    'com1': list(Analyzer.objects.filter(gateway=gateway, port='com1').values()),
                    'com2': list(Analyzer.objects.filter(gateway=gateway, port='com2').values()),
                    'e1': list(Analyzer.objects.filter(gateway=gateway, port='e1').values()),
                    'e2': list(Analyzer.objects.filter(gateway=gateway, port='e2').values())
                }

                # Construct the gateway data with analyzers_by_port
                gateway_data = {
                    'G_id': gateway.G_id,
                    'gateway_name': gateway.gateway_name,
                    'mac_address': gateway.mac_address,
                    'status': gateway.status,
                    'deploy_status': gateway.deploy_status,
                    'config': gateway.config,
                    'analyzers_by_port': analyzers_by_port
                }
                gateways_data.append(gateway_data)

            # Print gateways_data for debugging
            print('Gateways data being sent:', gateways_data)

            return JsonResponse({'Gateways': gateways_data}, status=200)

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=405)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_deployed_gateway_count(request):
    if request.method == "GET":
        try:
            user_id = request.GET.get('user_id')
            print('user_id:', user_id)

            if not user_id:
                return JsonResponse({'message': 'User ID is required'}, status=400)

            user = User.objects.filter(user_id=user_id).first()
            if not user:
                return JsonResponse({'message': 'User not found'}, status=404)

            deployed_count = Gateways.objects.filter(user_id=user_id, deploy_status="deployed").count()

            return JsonResponse({
                'user_id': user_id,
                'deployed_gateway_count': deployed_count
            }, status=200)

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=405)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_all_gateways(request):
    if request.method == "GET":
        try:
            user_id = request.GET.get("user_id")  
            role = request.GET.get("role")        
            if role == "admin":
                gateways = Gateways.objects.all()  # Admin sees all
            else:
                gateways = Gateways.objects.filter(user_id=user_id)  # Normal user sees only their gateways

            if not gateways.exists():
                return JsonResponse({'success': True, 'gateways': []}, status=200)

            gateways_data = []
            for gateway in gateways:
                created_by_user = User.objects.filter(user_id=gateway.created_by_id).first()
                admin_image = created_by_user.image if created_by_user else None

                gateways_data.append({
                    'G_id': gateway.G_id,
                    'gateway_name': gateway.gateway_name,
                    'mac_address': gateway.mac_address,
                    'status': gateway.status,
                    'deploy_status': gateway.deploy_status,
                    'config': gateway.config,
                    'created_by_id': gateway.created_by_id,
                    'user_id': gateway.user_id.user_id if gateway.user_id else None,
                    'user_image': gateway.user_id.image if gateway.user_id else None,
                    'admin_image': admin_image
                })

            return JsonResponse({'success': True, 'gateways': gateways_data}, status=200)

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=405)



def analyzer_data(analyzer):
    return {
        "analyzer_id": analyzer.analyzer_id,
        "name": analyzer.name,
        "company_name": analyzer.company_name,
        "type": analyzer.type,
        "status": analyzer.status,
        "gateway_id": analyzer.gateway.G_id,  # Gateway ID from ForeignKey
        "MOD_id": analyzer.MOD_id,
        "Date": analyzer.Date.strftime("%Y-%m-%d"),  # Format the date
        "port": analyzer.port,
    }

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_analyzer(request):
    if request.method == 'POST':
        try:
            # Parse request body
            data = json.loads(request.body)
            print('data',data)

            # Extract and validate required fields
            name = data.get('name')
            company_name = data.get('company_name')
            type = data.get('type')
            status = data.get('status', False)
            port = data.get('port')  # 'com1', 'com2', 'e1', 'e2'
            gateway_id = data.get('G_id')  # ID of the gateway
            MOD_id = data.get('MOD_id')  # MOD_id (must be unique)

            # Ensure required fields are present
            if not all([name, port, gateway_id, MOD_id]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            # Validate port choice
            if port not in dict(Analyzer.PORT_CHOICES):
                return JsonResponse({'error': f'Invalid port: {port}'}, status=400)

            # Retrieve the Gateway instance
            try:
                gateway_instance = Gateways.objects.get(G_id=gateway_id)
            except Gateways.DoesNotExist:
                return JsonResponse({'error': 'Invalid Gateway ID'}, status=404)

            # Check if an analyzer with the same name, gateway, and port exists
            analyzer = Analyzer.objects.filter(name=name, gateway=gateway_instance, port=port).first()

            if analyzer:
                # Update the existing analyzer
                analyzer.company_name = company_name
                analyzer.type = type
                analyzer.status = status
                analyzer.MOD_id = MOD_id

                # Save the updated analyzer
                analyzer.save()

                return JsonResponse({
                    'message': 'Analyzer updated successfully',
                    'analyzer': analyzer_data(analyzer)
                }, status=200)
            else:
                # Create a new analyzer
                analyzer = Analyzer.objects.create(
                    name=name,
                    company_name=company_name,
                    type=type,
                    status=status,
                    gateway=gateway_instance,
                    port=port,
                    MOD_id=MOD_id,
                )

                return JsonResponse({
                    'message': 'Analyzer created successfully',
                    'analyzer': analyzer_data(analyzer)
                }, status=201)

        except ValidationError as ve:
            return JsonResponse({'error': str(ve)}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=405)


def analyzer_data(analyzer):
    # Return the relevant data you need for the analyzer
    return {
        'analyzer_id': analyzer.analyzer_id,
        'name': analyzer.name,
        'company_name': analyzer.company_name,
        'type': analyzer.type,
        'status': analyzer.status,
        # 'values': {f"value{i}": getattr(analyzer, f"value{i}") for i in range(1, 21)},
        # 'addresses': {f"address{i}": getattr(analyzer, f"address{i}") for i in range(1, 21)},
        'port': analyzer.port,
        'gateway_id': analyzer.gateway.G_id,
    }
    
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_analyzers_by_gateway(request, gateway_id):
    try:
        # Retrieve the Gateway instance using the provided G_id
        gateway_instance = Gateways.objects.get(G_id=gateway_id)
        
        # Get all analyzers connected to the specified gateway
        analyzers = Analyzer.objects.filter(gateway=gateway_instance)
        
        # Organize the analyzers by port (com1, com2, e1, e2)
        analyzers_by_port = {
            'com1': [],
            'com2': [],
            'e1': [],
            'e2': [],
        }
        
        for analyzer in analyzers:
            # Prepare analyzer data to include necessary fields
            analyzer_data = {
                'analyzer_id': analyzer.analyzer_id,
                'name': analyzer.name,
                'company_name': analyzer.company_name,
                'type': analyzer.type,
                'status': analyzer.status,
                'MOD_id': analyzer.MOD_id,
                'Date': analyzer.Date.strftime('%Y-%m-%d'),  # Format date
                'port': analyzer.port,  # Port the analyzer is connected to
            }
            # Append the analyzer data to the respective port category
            if analyzer.port in analyzers_by_port:
                analyzers_by_port[analyzer.port].append(analyzer_data)
        
        # Return the gateway and organized analyzers data
        return JsonResponse({
            'gateway_name': gateway_instance.gateway_name,
            'gateway_id': gateway_instance.G_id,
            'analyzers_by_port': analyzers_by_port,
        }, status=200)

    except Gateways.DoesNotExist:
        return JsonResponse({'error': 'Gateway not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_ports(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"Received data: {data}")
            
            port_type = data.get('port_type')
            G_id = data.get('G_id')
            
            if not port_type or not G_id:
                return JsonResponse({'message': 'Port type and Gateway id required'}, status=400)
            
            try:
                gateway = Gateways.objects.get(G_id=G_id)
                print(f"Gateway found: {gateway}")
            except Gateways.DoesNotExist:
                return JsonResponse({'message': 'Gateway not found'}, status=404)
            
            if port_type.lower() == 'com1':
                port = Com1.objects.create(G_id=gateway)
            elif port_type.lower() == 'com2':
                port = Com2.objects.create(G_id=gateway)
            elif port_type.lower() == 'e1':
                port = E1.objects.create(G_id=gateway)
            elif port_type.lower() == 'e2':
                port = E2.objects.create(G_id=gateway)
            else:
                return JsonResponse({'message': 'Invalid port type'}, status=400)

            print(f"{port_type} created with ID: {port.pk}")
            return JsonResponse({'message': f'{port_type} created successfully', 'ID': port.pk}, status=201)

        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    print(f"Invalid request method: {request.method}")
    return JsonResponse({'message': 'Invalid request method'}, status=405)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_ports(request):
    if request.method == 'GET':
        try:
            port_type = request.GET.get('port_type')
            G_id = request.GET.get('G_id')

            if not port_type or not G_id:
                return JsonResponse({'message': 'Port type and Gateway id required'}, status=400)
            
            try:
                gateway = Gateways.objects.get(G_id=G_id)
                print(f"Gateway found: {gateway}")
            except Gateways.DoesNotExist:
                return JsonResponse({'message': 'Gateway not found'}, status=404)

            # Fetch based on port type
            if port_type.lower() == 'com1':
                ports = Com1.objects.filter(G_id=gateway)
            elif port_type.lower() == 'com2':
                ports = Com2.objects.filter(G_id=gateway)
            elif port_type.lower() == 'e1':
                ports = E1.objects.filter(G_id=gateway)
            elif port_type.lower() == 'e2':
                ports = E2.objects.filter(G_id=gateway)
            else:
                return JsonResponse({'message': 'Invalid port type'}, status=400)

            # Prepare response data
            port_list = [{'id': port.pk, 'G_id': port.G_id.G_id} for port in ports]
            
            return JsonResponse({'message': f'{port_type} fetched successfully', 'data': port_list}, status=200)

        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    print(f"Invalid request method: {request.method}")
    return JsonResponse({'message': 'Invalid request method'}, status=405)

# fetch analyzer on he basis of specefic port
def fetch_analyzers_by_port(request, port_id):
    try:
        # Try to find the port in each model (com1, com2, e1, e2) by port_id
        port = None
        port_type = None

        try:
            port = Com1.objects.get(com1_id=port_id)
            port_type = 'com1'
        except Com1.DoesNotExist:
            pass

        if not port:
            try:
                port = Com2.objects.get(com2_id=port_id)
                port_type = 'com2'
            except Com2.DoesNotExist:
                pass

        if not port:
            try:
                port = E1.objects.get(E1_id=port_id)
                port_type = 'e1'
            except E1.DoesNotExist:
                pass

        if not port:
            try:
                port = E2.objects.get(E2_id=port_id)
                port_type = 'e2'
            except E2.DoesNotExist:
                pass

        # If no port is found, return an error
        if not port:
            return JsonResponse({'message': 'Port not found'}, status=404)

        # Fetch analyzers based on the detected port type
        if port_type == 'com1':
            analyzers = list(
                Analyzer.objects.filter(com1=port).values(
                    'analyzer_id', 'name', 'company_name', 'type', 'status',
                    'value1', 'address1', 'value2', 'address2', 'value3', 'address3',
                    'value4', 'address4', 'value5', 'address5', 'value6', 'address6',
                    'value7', 'address7', 'value8', 'address8', 'value9', 'address9',
                    'value10', 'address10', 'value11', 'address11', 'value12', 'address12',
                    'value13', 'address13', 'value14', 'address14', 'value15', 'address15',
                    'value16', 'address16', 'value17', 'address17', 'value18', 'address18',
                    'value19', 'address19', 'value20', 'address20'
                )
            )
        elif port_type == 'com2':
            analyzers = list(
                Analyzer.objects.filter(com2=port).values(
                    'analyzer_id', 'name', 'company_name', 'type', 'status',
                    'value1', 'address1', 'value2', 'address2', 'value3', 'address3',
                    'value4', 'address4', 'value5', 'address5', 'value6', 'address6',
                    'value7', 'address7', 'value8', 'address8', 'value9', 'address9',
                    'value10', 'address10', 'value11', 'address11', 'value12', 'address12',
                    'value13', 'address13', 'value14', 'address14', 'value15', 'address15',
                    'value16', 'address16', 'value17', 'address17', 'value18', 'address18',
                    'value19', 'address19', 'value20', 'address20'
                )
            )
        elif port_type == 'e1':
            analyzers = list(
                Analyzer.objects.filter(e1=port).values(
                    'analyzer_id', 'name', 'company_name', 'type', 'status',
                    'value1', 'address1', 'value2', 'address2', 'value3', 'address3',
                    'value4', 'address4', 'value5', 'address5', 'value6', 'address6',
                    'value7', 'address7', 'value8', 'address8', 'value9', 'address9',
                    'value10', 'address10', 'value11', 'address11', 'value12', 'address12',
                    'value13', 'address13', 'value14', 'address14', 'value15', 'address15',
                    'value16', 'address16', 'value17', 'address17', 'value18', 'address18',
                    'value19', 'address19', 'value20', 'address20'
                )
            )
        elif port_type == 'e2':
            analyzers = list(
                Analyzer.objects.filter(e2=port).values(
                    'analyzer_id', 'name', 'company_name', 'type', 'status',
                    'value1', 'address1', 'value2', 'address2', 'value3', 'address3',
                    'value4', 'address4', 'value5', 'address5', 'value6', 'address6',
                    'value7', 'address7', 'value8', 'address8', 'value9', 'address9',
                    'value10', 'address10', 'value11', 'address11', 'value12', 'address12',
                    'value13', 'address13', 'value14', 'address14', 'value15', 'address15',
                    'value16', 'address16', 'value17', 'address17', 'value18', 'address18',
                    'value19', 'address19', 'value20', 'address20'
                )
            )
        else:
            return JsonResponse({'message': 'Invalid port type'}, status=400)

        # Return the JSON response with the port and its connected analyzers
        response_data = {
            'port_id': port_id,
            'port_type': port_type,
            'analyzers': analyzers
        }

        return JsonResponse(response_data, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
#for specefic user
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def Fetch_Projects(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')  

            if not user_id:
                return JsonResponse({'error': 'User ID is required'}, status=400)

            try:
                user = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'User does not exist'}, status=404)

            projects = Project_Manager.objects.filter(user_id=user)

            projects_data = [
                {
                    'project_id': project.PM_id,  
                    'name': project.name,
                    'user': {
                        'firstname': user.firstname,
                        'lastname': user.lastname
                    }
                }
                for project in projects
            ]


            return JsonResponse(projects_data, safe=False, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=403)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

#fetch total projects
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_all_projects(request):
    if request.method == 'GET':
        try:
            projects = Project_Manager.objects.all()
            
            project_data = [
                {
                    'Pm_id' : project.PM_id,
                    'name' : project.name,
                    'user' : {
                        'user_id': project.user_id.user_id,
                        'firstname': project.user_id.firstname,
                        'lastname' : project.user_id.lastname
                    },
                    'is-active' : project.is_active
                }
                for project in projects
            ]
            return JsonResponse(project_data , safe=False , status=200)
        except Exception as e:
            return JsonResponse({'error' : str(e)}, status=500)
    return JsonResponse({'error' : 'invalid request method'})
        


#for admin total hardware count
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def total_hardware_count(request):
    try:
        total_hardware = Hardware.objects.count()
        return JsonResponse({'Total_count' : total_hardware}, status=200)
    except Exception as e :
        return JsonResponse({'Error' : str(e)}, status=400)
    
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def total_connected_hardware(request):
    
        total_hardware = Hardware.objects.count()
        connected_hardware = Hardware.objects.filter(is_connected=True).count()
        return JsonResponse({
            'total Hardware' : total_hardware,
            'connected_Hardware' : connected_hardware
        })
        
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def total_project(request):
    try:
        total_project = Project_Manager.objects.count()
        return JsonResponse({'total_project' : total_project}, status=200)
    except Exception as e:
        return JsonResponse({'error' : str(e)}, status=400)
    
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def active_project(request):
    total_project = Project_Manager.objects.count()
    active_project = Project_Manager.objects.filter(is_active=True).count()
    return JsonResponse({
        'total_project' : total_project,
        'active_project' : active_project
        
    })
    
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetches_total_hardware(request):
    if request.method == 'GET':
        try:
            hardware_list = Hardware.objects.all().values(
                'hardware_id',
                'project_id',
                'name',
                'serial_number',
                'is_connected',
                'connected_at'
            )
            return JsonResponse(list(hardware_list), safe=False, status=200)
        except Exception as e:
            return JsonResponse({'error' : str(e)}, status=400)
    return JsonResponse({'error' : 'invalid request method'}, status=405)


#fetch assigned Hardware
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_assigned_hardware(request):
    try:
        assigned_hardware = Hardware.objects.filter(user__isnull=False).values('hardware_id' , 'name' , 'user__firstname' , 'user__lastname')
        
        assigned_hardware_list = list(assigned_hardware)
        return JsonResponse(assigned_hardware_list, safe=False, status=200)
    except Exception as e :
        return JsonResponse({'error' : str(e)}, status=401)
    
# -----Box model viewss---------

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_box(request):
    if request.method == "POST":
        try:
            # Parse JSON data
            data = json.loads(request.body)
            box_data = data.get("box")  # Access "box" key
            if not box_data:
                return JsonResponse({"message": "'box' key is required in the JSON data."}, status=400)

            name = box_data.get("name")
            content = box_data.get("content")

            # Validate name and content
            if not name or not isinstance(content, list):
                return JsonResponse({"message": "Name and content (as a list) are required."}, status=400)

            # Create a new Box entry
            box = Box.objects.create(name=name, content=content)

            return JsonResponse({"message": "New box created.", "box": {"name": box.name, "content": box.content}}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON format."}, status=400)
        except Exception as e:
            logger.error(f"Error: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"message": "Method not allowed"}, status=405)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_boxes(request):
    try:
        
        latest_box = Box.objects.latest('box')  

        return JsonResponse({
            'box': {
                'name': latest_box.name,
                'content': latest_box.content
            }
        }, status=200)

    except Box.DoesNotExist:
    
        return JsonResponse({'message': 'No boxes found'}, status=404)
    except Exception as e:
    
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    
    

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_gateway(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            gateway_name = data.get('gateway')
            ports = data.get('ports', [])
        
            # Use `get_or_create` to ensure uniqueness based on `gateway_name`
            gateway, created = Gateway.objects.get_or_create(gateway_name=gateway_name)
        
            current_timestamp = timezone.now()

            for port_devices in ports:
                for device_data in port_devices:
                    # Check if a device with the same name exists in this gateway
                    existing_device = gateway.devices.filter(name=device_data.get('name')).first()
                    
                    if existing_device:
                        # If the device exists, update its attributes
                        existing_device.device_type = device_data.get('device_type')
                        existing_device.type = device_data.get('type')
                        existing_device.status = device_data.get('status')
                        existing_device.value = device_data.get('value')
                        existing_device.timestamp = current_timestamp
                        existing_device.save()
                    else:
                        # Create a new device and associate it with the gateway
                        device = Device.objects.create(
                            device_type=device_data.get('device_type'),
                            name=device_data.get('name'),
                            type=device_data.get('type'),
                            status=device_data.get('status'),
                            value=device_data.get('value'),
                            timestamp=current_timestamp
                        )
                        gateway.devices.add(device)
            
            return JsonResponse({'message': 'Gateway updated successfully'}, status=200)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'message': 'Invalid request method'}, status=405)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_gateway(request, gateway_name):
    try:
    
        gateway = Gateway.objects.get(gateway_name=gateway_name)

        latest_timestamp = gateway.devices.order_by('-timestamp').values('timestamp').first()
        
        if not latest_timestamp:
            return JsonResponse({"error": "No data found for this gateway"}, status=404)
        
    
        latest_devices = gateway.devices.filter(timestamp=latest_timestamp['timestamp'])

    
        grouped_devices = {
            "com1": [],
            "com2": [],
            "E1": [],
            "E2": []
        }


        for device in latest_devices:
            device_info = {
                "device_type": device.device_type,
                "name": device.name,
                "type": device.type,
                "status": device.status,
                "value": device.value
            }
            if device.device_type in grouped_devices:
                grouped_devices[device.device_type].append(device_info)

        # Structure the response in the requested format
        response_data = {
            "gateway": gateway.gateway_name,
            "ports": [
                grouped_devices["com1"],
                grouped_devices["com2"],
                grouped_devices["E1"],
                grouped_devices["E2"]
            ]
        }

        return JsonResponse(response_data, status=200)

    except Gateway.DoesNotExist:
        return JsonResponse({"error": "Gateway not found"}, status=404)
    
    
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_all_gateways(request):
    try:
        # Retrieve all gateways from the database
        all_gateways = Gateway.objects.all()

        if not all_gateways.exists():
            return JsonResponse({"error": "No gateways found"}, status=404)

        # List to store all gateway data
        response_data = []

        for gateway in all_gateways:
            # Find the latest timestamp for devices associated with the current gateway
            latest_timestamp = gateway.devices.order_by('-timestamp').values('timestamp').first()
            
            if not latest_timestamp:
                # If no devices are found, add an empty entry for the gateway
                gateway_info = {
                    "gateway": gateway.gateway_name,
                    "ports": {
                        "com1": [],
                        "com2": [],
                        "E1": [],
                        "E2": []
                    }
                }
            else:
                # Retrieve devices with the latest timestamp
                latest_devices = gateway.devices.filter(timestamp=latest_timestamp['timestamp'])

                # Group devices by device_type
                grouped_devices = {
                    "com1": [],
                    "com2": [],
                    "E1": [],
                    "E2": []
                }

                for device in latest_devices:
                    device_info = {
                        "device_type": device.device_type,
                        "name": device.name,
                        "type": device.type,
                        "status": device.status,
                        "value": device.value
                    }
                    if device.device_type in grouped_devices:
                        grouped_devices[device.device_type].append(device_info)

                # Prepare the structured data for the current gateway
                gateway_info = {
                    "gateway": gateway.gateway_name,
                    "ports": {
                        "com1": grouped_devices["com1"],
                        "com2": grouped_devices["com2"],
                        "E1": grouped_devices["E1"],
                        "E2": grouped_devices["E2"]
                    }
                }

            # Add the current gateway's info to the response list
            response_data.append(gateway_info)

        # Return the full list of gateways and their data
        return JsonResponse(response_data, safe=False, status=200)

    except Exception as e:
        # Handle unexpected errors
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    
# value data for chart---------------------------------
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_value_data(request , gateway_name):
    
    try:
        gateway = Gateway.objects.get(gateway_name=gateway_name)
        
        values_by_port = {
            "com1" : [],
            "com2" : [],
            "E1" : [],
            "E2" : []
        }
        for device in gateway.devices.all():
            if device.device_type in values_by_port:
                values_by_port[device.device_type].append(device.value)
                
        response_data = {
            "title" :f"{gateway.gateway_name}",
            "series" :[
                {"name" : "com1", "data" : values_by_port["com1"]},
                {"name" : "com2", "data" : values_by_port["com2"]},
                {"name" : "E1", "data" : values_by_port["E1"]},
                {"name" : "E2", "data" : values_by_port["E2"]},
            ]
        }  
        return JsonResponse(response_data , status=200)
    except Gateway.DoesNotExist:
        return JsonResponse({'message' : 'Gateway not found'}, status=404)
    
# specefic type data--------------------------------------last 20 values
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_device_data(request, gateway_name, device_type, device_subtype):
    try:
        
        gateway = Gateway.objects.get(gateway_name=gateway_name)

    
        filtered_devices = gateway.devices.filter(
            device_type__iexact=device_type,
            name__iexact=device_subtype
        ).order_by('-timestamp')[:20]

        if not filtered_devices.exists():
            return JsonResponse(
                {"error": f"No data found for {device_type} {device_subtype} in gateway {gateway_name}"},
                status=404
            )

        
        device_list = []
        for device in filtered_devices:
            device_info = {
                "device_type": device.device_type, 
                "name": device.name,         
                "type": device.type,      
                "status": device.status,  
                "value": device.value,   
                "timestamp": device.timestamp.isoformat() 
            }
            device_list.append(device_info)

        # Structure the response in the requested format
        response_data = {
            "gateway": gateway.gateway_name,
            "ports": [
                device_list  # Devices are grouped as a single list for the requested `device_type` and `type`
            ]
        }

        return JsonResponse(response_data, status=200)

    except Gateway.DoesNotExist:
        return JsonResponse({"error": "Gateway not found"}, status=404)

# fetching whole data
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_whole_device_data(request, gateway_name, device_type, device_subtype):
    try:
        
        gateway = Gateway.objects.get(gateway_name=gateway_name)

    
        filtered_devices = gateway.devices.filter(
            device_type__iexact=device_type,
            name__iexact=device_subtype
        )

        if not filtered_devices.exists():
            return JsonResponse(
                {"error": f"No data found for {device_type} {device_subtype} in gateway {gateway_name}"},
                status=404
            )

        
        device_list = []
        for device in filtered_devices:
            device_info = {
                "device_type": device.device_type, 
                "name": device.name,         
                "type": device.type,      
                "status": device.status,  
                "value": device.value,   
                "timestamp": device.timestamp.isoformat() 
            }
            device_list.append(device_info)

        # Structure the response in the requested format
        response_data = {
            "gateway": gateway.gateway_name,
            "ports": [
                device_list  # Devices are grouped as a single list for the requested `device_type` and `type`
            ]
        }

        return JsonResponse(response_data, status=200)

    except Gateway.DoesNotExist:
        return JsonResponse({"error": "Gateway not found"}, status=404)
    
    
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def assign_gateway_to_project(request):
    """
    Assign a gateway to a project.
    """
    if request.method == 'POST':
        try:
            # Get the data from the request body
            data = json.loads(request.body)
            project_id = data.get("project_id")
            gateway_id = data.get("gateway_id")

            if not project_id or not gateway_id:
                return JsonResponse({"error": "Missing project_id or gateway_id"}, status=400)

            # Fetch the project and gateway objects
            project = get_object_or_404(Project_Manager, PM_id=project_id)
            gateway = get_object_or_404(Gateways, G_id=gateway_id)

            # Assign the gateway to the project
            gateway.project = project
            gateway.save()

            return JsonResponse({
                "message": f"Gateway {gateway.gateway_name} successfully assigned to project {project.name}"
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return HttpResponse(status=405)  # Method Not Allowed

    
def get_gateways_for_project(request):
    """
    Get a list of all gateways assigned to a project.
    """
    if request.method == 'GET':
        try:
            project_id = request.GET.get("project_id")

            # Fetch the project
            project = get_object_or_404(Project_Manager, PM_id=project_id)

            # Fetch all gateways associated with the project
            gateways = Gateways.objects.filter(project=project)

            # Prepare the data to return
            gateways_data = [{
                "G_id": gateway.G_id,
                "gateway_name": gateway.gateway_name,
                "mac_address": gateway.mac_address,
                "status": gateway.status,
                "deploy_status": gateway.deploy_status,
                "config": gateway.config,
            } for gateway in gateways]

            return JsonResponse({"gateways": gateways_data}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return HttpResponse(status=405)  # Method Not Allowed
    
# create Metadata **********************************************
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_metadata(request):
    if request.method == "POST":
        try:
            # Parse the JSON body
            data = json.loads(request.body)

            # Extract required fields
            analyzer_id = data.get("analyzer_id")
            mac_address = data.get("mac_address")
            values = data.get("values", {})  # Expecting a dictionary of values

            # Validate analyzer_id
            if not analyzer_id:
                return JsonResponse({"message": "Analyzer ID is required"}, status=400)

            # Fetch the Analyzer and Gateway
            analyzer = Analyzer.objects.filter(analyzer_id=analyzer_id).first()
            if not analyzer:
                return JsonResponse({"message": "Analyzer not found"}, status=404)

            gateway = analyzer.gateway
            if not gateway:
                return JsonResponse({"message": "Gateway associated with this analyzer not found"}, status=404)

            # Validate mac_address matches the gateway
            if gateway.mac_address != mac_address:
                return JsonResponse({"message": "MAC address does not match the gateway"}, status=400)

            # Create the MetaData instance
            metadata = MetaData.objects.create(
                mac_address=mac_address,
                gateway=gateway,
                MOD_id=analyzer.MOD_id,
                analyzer=analyzer,
                **{
                    f"value{i}_name": values.get(f"value{i}_name", "")
                    for i in range(1, 21)
                },
                **{
                    f"value{i}_address": values.get(f"value{i}_address", "")
                    for i in range(1, 21)
                },
                **{
                    f"value{i}_value": values.get(f"value{i}_value", None)
                    for i in range(1, 21)
                },
            )

            # Respond with the created metadata
            return JsonResponse(
                {
                    "message": "MetaData created successfully",
                    "metadata_id": metadata.MD_id,
                },
                status=201,
            )

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"message": "Invalid request method"}, status=405)


#  get metadata****************************************************************
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_metadata(request, analyzer_id):
    if request.method == "GET":
        try:
            # Fetch the latest metadata for the given analyzer_id
            metadata = MetaData.objects.filter(analyzer__analyzer_id=analyzer_id).order_by('-timestamp').first()

            if not metadata:
                return JsonResponse({"message": "No metadata found for this analyzer"}, status=404)

            # Prepare metadata response
            metadata_response = {
                "MD_id": metadata.MD_id,
                "mac_address": metadata.mac_address,
                "MOD_id": metadata.MOD_id,
                "values": {
                    f"value{i}_name": getattr(metadata, f"value{i}_name") for i in range(1, 21)
                },
                "values_address": {
                    f"value{i}_address": getattr(metadata, f"value{i}_address") for i in range(1, 21)
                },
                "values_value": {
                    f"value{i}_value": getattr(metadata, f"value{i}_value") for i in range(1, 21)
                },
                "timestamp": metadata.timestamp,  # Include timestamp for the latest record
            }

            return JsonResponse({"metadata": metadata_response}, status=200)

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"message": "Invalid request method"}, status=405)

# for getting the specefic value data and show in highchart****************************************************************
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_analyzer_value_data(request, analyzer_id, value_name):
    if request.method == 'GET':
        try:
            # Parse date range parameters
            from_date = request.GET.get('from', None)
            to_date = request.GET.get('to', None)

            if from_date and to_date:
                from_date = datetime.strptime(from_date, '%Y-%m-%d')
                to_date = datetime.strptime(to_date, '%Y-%m-%d')
            else:
                # Default to the last 30 days if no date range is provided
                to_date = datetime.now()
                from_date = to_date - timedelta(days=30)  # Corrected usage of timedelta

            # Fetch the data for the specified analyzer and value_name
            data = MetaData.objects.filter(analyzer__analyzer_id=analyzer_id, timestamp__range=[from_date, to_date])
            value_data = []
            categories = []

            for item in data:
                # Corrected the attribute name access here
                value = getattr(item, f"{value_name}")  # Dynamically access the correct value field
                timestamp = item.timestamp
                value_data.append([int(timestamp.timestamp() * 1000), value])  # Ensure the timestamp is an integer
                categories.append(timestamp.strftime('%Y-%m-%d %H:%M:%S'))

            # Prepare the response for Highcharts
            response = {
                'categories': categories,
                'series': [{
                    'name': value_name,
                    'data': value_data
                }]
            }

            return JsonResponse(response, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def post_metadata(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            print(data)

            mac_address = data.get("mac_address")
            if not mac_address:
                return JsonResponse({"error": "MAC address is required"}, status=400)

            try:
                gateway = Gateways.objects.get(mac_address=mac_address)
            except Gateways.DoesNotExist:
                return JsonResponse({"error": "MAC address not matched with any gateway"}, status=404)

            total_power = data.get("total_power", 0)
            setpoint1 = data.get("setpoint1", 0)
            setpoint2 = data.get("setpoint2", 0)
            total_grid = data.get("total_grid", 0)
            total_Generator = data.get("total_Generator", 0)
            total_solar = data.get("total_solar", 0)

            
            valid_analyzers = []

            ports_data = data.get("ports", [])  
            for port_analyzers in ports_data:
                for analyzer_data in port_analyzers:
                    port_name = analyzer_data.get("port_name")
                    if port_name:
                        port_name = port_name.split('/')[-1].split('.')[0]

                    analyzer_name = analyzer_data.get("name")
                    analyzer_type = analyzer_data.get("type")
                    analyzer_status = analyzer_data.get("status")
                    values = analyzer_data.get("values", [])

                    if not (port_name and analyzer_name and analyzer_type):
                        return JsonResponse({"error": "Port name, analyzer name, and type are required"}, status=400)

                    analyzer, _ = Analyzer.objects.update_or_create(
                        name=analyzer_name,
                        gateway=gateway,
                        port=port_name,
                        defaults={
                            "type": analyzer_type,
                            "status": analyzer_status,
                            "company_name": analyzer_data.get("company_name", "Unknown"),
                        }
                    )
                    valid_analyzers.append(analyzer)

                    metadata = MetaData.objects.create(
                        gateway=gateway,
                        analyzer=analyzer,
                        mac_address=gateway.mac_address,
                        MOD_id=f"{gateway.gateway_name}_{port_name}_{analyzer_name}_{uuid.uuid4().hex[:8]}",
                        total_power=total_power,  
                        setpoint1=setpoint1,  
                        setpoint2=setpoint2,
                        total_grid=total_grid,
                        total_Generator=total_Generator,
                        total_solar=total_solar,
                    )

                    for i, value in enumerate(values, start=1):
                        if i > 20:
                            break
                        setattr(metadata, f"value{i}_name", value.get("name"))
                        setattr(metadata, f"value{i}_address", value.get("address"))
                        setattr(metadata, f"value{i}_value", value.get("value"))
                        setattr(metadata, f"value{i}_unit", value.get("unit"))
                    metadata.save()

            Analyzer.objects.filter(gateway=gateway).exclude(analyzer_id__in=[a.analyzer_id for a in valid_analyzers]).delete()

            return JsonResponse({
                "message": "Data successfully created or updated",
                "total_power": total_power,
                "setpoint1": setpoint1,
                "setpoint2": setpoint2,
                "total_grid": total_grid,
                "total_Generator": total_Generator,
                "total_solar": total_solar
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

# Add debug logs
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_metadata(request):
    if request.method == "GET":
        try:
            gateway_name = request.GET.get("gateway")
            if not gateway_name:
                return JsonResponse({"error": "Gateway name is required"}, status=400)

            gateway = Gateways.objects.get(gateway_name=gateway_name)
            analyzers = Analyzer.objects.filter(gateway=gateway)

            ports_data = []
            for port_name in ["COM_1", "COM_2", "e1", "e2"]:
                port_analyzers = []
                port_analyzers_qs = analyzers.filter(port=port_name)
                for analyzer in port_analyzers_qs:
                    metadata = MetaData.objects.filter(analyzer=analyzer).order_by('-timestamp').first()
                    values = [
                        {
                            "name": getattr(metadata, f"value{i}_name", None),
                            "address": getattr(metadata, f"value{i}_address", None),
                            "value": getattr(metadata, f"value{i}_value", None),
                            "unit": getattr(metadata, f"value{i}_unit", None), 
                        }
                        for i in range(1, 21)
                        if getattr(metadata, f"value{i}_name", None)
                    ]
                    port_analyzers.append({
                        "port_name": port_name,
                        "name": analyzer.name,
                        "type": analyzer.type,
                        "status": analyzer.status,
                        "values": values,
                    })
                ports_data.append({"port_name": port_name, "analyzers": port_analyzers})

            # Log the response
            response = {"gateway": gateway_name, "ports": ports_data}
            # print("Fetch Metadata Response:", response)
            return JsonResponse(response, status=200)

        except Exception as e:
            print("Fetch Metadata Error:", str(e))
            return JsonResponse({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_highchart_data(request):
    if request.method == "GET":
        try:
            # Get query parameters
            gateway_name = request.GET.get("gateway")
            value_name = request.GET.get("value_name")
            from_date = request.GET.get("from_date")
            to_date = request.GET.get("to_date")
            if not gateway_name or not value_name:
                return JsonResponse({"error": "Gateway name and value name are required"}, status=400)
            # Convert the date strings to timezone-aware datetime objects
            if from_date:
                from_date = timezone.make_aware(
                    datetime.strptime(from_date, "%Y-%m-%d"), timezone.get_current_timezone()
                )
            if to_date:
                to_date = timezone.make_aware(
                    datetime.combine(
                        datetime.strptime(to_date, "%Y-%m-%d"), datetime.max.time()
                    ),
                    timezone.get_current_timezone()
                )
            # Fetch the gateway
            try:
                gateway = Gateways.objects.get(gateway_name=gateway_name)
            except Gateways.DoesNotExist:
                return JsonResponse({"error": "Gateway not found"}, status=404)
            # Fetch analyzers for the gateway
            analyzers = Analyzer.objects.filter(gateway=gateway)
            if not analyzers.exists():
                return JsonResponse({"error": "No analyzers found for the gateway"}, status=404)
            # Prepare Highcharts data
            highchart_data = []
            for port_name in ["COM_1", "COM_2", "e1", "e2"]:
                port_analyzers = analyzers.filter(port=port_name)
                port_data = {
                    "name": port_name,
                    "data": []
                }
                for analyzer in port_analyzers:
                    metadata_entries = MetaData.objects.filter(analyzer=analyzer)
                    if from_date:
                        metadata_entries = metadata_entries.filter(timestamp__gte=from_date)
                    if to_date:
                        metadata_entries = metadata_entries.filter(timestamp__lte=to_date)
                    value_series = []
                    unit = None
                    value_dict = defaultdict(float)
                    for metadata in metadata_entries:
                        for i in range(1, 21):
                            name = getattr(metadata, f"value{i}_name", None)
                            value = getattr(metadata, f"value{i}_value", None)
                            current_unit = getattr(metadata, f"value{i}_unit", None)
                            if name == value_name and isinstance(value, (int, float)):
                                timestamp_str = metadata.timestamp.strftime("%Y-%m-%d")
                                value_dict[timestamp_str] += value
                            if not unit:
                                unit = current_unit
                    # Convert the dictionary to a sorted list
                    value_series = sorted(value_dict.items())
                    if value_series:
                        port_data["data"].append({
                            "name": analyzer.name,
                            "data": value_series,
                            "unit": unit
                        })
                
                # **Sort the analyzers inside port_data["data"] by their earliest timestamp**
                port_data["data"].sort(key=lambda x: x["data"][0][0] if x["data"] else float("inf"))
                if port_data["data"]:
                    highchart_data.append(port_data)
            return JsonResponse({
                "gateway": gateway_name,
                "value_name": value_name,
                "ports": highchart_data
            }, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)



@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def analyzer_values(request, gateway_name):
    if request.method == "GET":
        try:
            # Fetch the gateway by name
            gateway = Gateways.objects.filter(gateway_name=gateway_name).first()
            if not gateway:
                return JsonResponse({"error": "Gateway not found"}, status=404)

            # Initialize the response structure
            response_data = {
                "gateway_name": gateway.gateway_name,
                "mac_address": gateway.mac_address,
                "analyzers": [],
            }

            # Fetch all analyzers associated with the gateway
            analyzers = Analyzer.objects.filter(gateway=gateway)

            # Iterate through each analyzer
            for analyzer in analyzers:
                # Get the latest metadata for the analyzer
                latest_metadata = (
                    MetaData.objects.filter(analyzer=analyzer)
                    .order_by("-created_at")  # Assuming `created_at` is a timestamp field
                    .first()
                )

                if latest_metadata:
                    # Gather the 20 values dynamically
                    values = []
                    for i in range(1, 21):  # Assuming 20 dynamic value fields
                        value_name = getattr(latest_metadata, f"value{i}_name", None)
                        value_address = getattr(latest_metadata, f"value{i}_address", None)
                        value_value = getattr(latest_metadata, f"value{i}_value", None)

                        if value_name or value_address or value_value:
                            values.append({
                                "name": value_name,
                                "address": value_address,
                                "value": value_value,
                            })

                    # Append analyzer data to the response
                    response_data["analyzers"].append({
                        "name": analyzer.name,
                        "type": analyzer.type,
                        "status": analyzer.status,
                        "company_name": analyzer.company_name,
                        "values": values,
                    })

            return JsonResponse(response_data, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)



# getting the gateway nmae and mac address for dropdown in project manager react jsx
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetch_deployed_gateways_name_mac(request):
    if request.method == "GET":
        try:
            # Get project_id from query parameters
            project_id = request.GET.get('project_id')
            if not project_id:
                return JsonResponse({'message': 'Project ID is required'}, status=400)

            # Debug: Log the incoming project_id
            print(f"Fetching deployed gateways for Project ID: {project_id}")

            # Fetch gateways with 'deployed' status and matching project_id
            deployed_gateways = Gateways.objects.filter(deploy_status='deployed', project_id=project_id)

            if not deployed_gateways.exists():
                print(f"No deployed gateways found for Project ID: {project_id}")
                return JsonResponse({'message': 'No deployed gateways found for the project'}, status=404)

            # Prepare response data with only gateway_name and mac_address
            gateways_data = [
                {
                    'gateway_name': gateway.gateway_name,
                    'mac_address': gateway.mac_address
                }
                for gateway in deployed_gateways
            ]

            # Debug: Confirm the number of gateways found
            print(f"Found {len(gateways_data)} gateways for Project ID: {project_id}")

            return JsonResponse({'deployed_gateways': gateways_data}, status=200)

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=405)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_power_data(request):
    try:
        gateway_id = request.GET.get('gateway_id')  # 👈 now expecting gateway_id

        if not gateway_id:
            return JsonResponse({"error": "Missing gateway_id in request"}, status=400)

        metadata_list = MetaData.objects.filter(gateway_id=gateway_id).values(
            'setpoint1', 'setpoint2', 'total_power' , 'total_grid', 'total_Generator', 'total_solar'
        ).order_by('-MD_id')[:10]

        if metadata_list.exists():
            return JsonResponse({"data": list(metadata_list)}, safe=False)
        else:
            return JsonResponse({"error": "No data found for this gateway"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
    
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def total_admin(request):
    if request.method == 'GET':
        try:
            # Count only users with role='user'
            admin_count = User.objects.filter(role='admin').count()
            return JsonResponse({'admin_users': admin_count}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'invalid method'}, status=405)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def admin_detail(request):
    if request.method == 'GET':
        try:
            admins = User.objects.filter(role='admin')

            data = []
            for admin in admins:
                total_users = User.objects.filter(role='user').filter(hardware__in=admin.hardware.all()).distinct().count()

                total_cr_ids = admincr.objects.filter(admin_id=admin.user_id).count()
                total_projects = Project_Manager.objects.filter(user_id=admin.user_id).count()
                data.append({
                    'id': admin.user_id,
                    'username': f"{admin.firstname} {admin.lastname}",
                    'email': admin.email,
                    'totalUsers': total_cr_ids,
                    'totalProjects': total_projects
                })

            return JsonResponse(data, safe=False, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=405)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def total_projecta(request):
    try:
        if request.method == 'GET':
            # Simply count all projects
            total_projects = Project_Manager.objects.count()
            return JsonResponse({'total_project': total_projects}, status=200)

        return JsonResponse({'error': 'Invalid request method'}, status=405)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def total_project_user(request):
    try:
        if request.method == 'GET':
            user_id = request.GET.get('user_id')  # Get user_id from query params

            if user_id:
                total_projects = Project_Manager.objects.filter(user_id=user_id).count()
            else:
                total_projects = Project_Manager.objects.count()

            return JsonResponse({'total_project': total_projects}, status=200)

        return JsonResponse({'error': 'Invalid request method'}, status=405)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_total_gateways_user(request):
    if request.method == "GET":
        try:
            user_id = request.GET.get("user_id")
            if not user_id:
                return JsonResponse({"error": "user_id is required"}, status=400)
            
            # Clean user_id just in case
            user_id = ''.join(filter(str.isdigit, user_id))

            # Filter Gateways by user_id
            total_gateways_count = Gateways.objects.filter(user_id=user_id).count()

            return JsonResponse({
                "message": "Gateways retrieved successfully",
                "gateways_count": total_gateways_count
            }, status=200)

        except Exception as e:
            return JsonResponse({
                "error": str(e)
            }, status=400)

    return JsonResponse({"error": "Invalid method"}, status=405)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def admin_detail_superadmin(request):
    if request.method == 'GET':
        try:
            admins = User.objects.filter(role='admin')

            data = []
            for admin in admins:
                data.append({
                    'id': admin.user_id,
                    'firstname': admin.firstname, 
                    'lastname': admin.lastname,
                    'email': admin.email,
                    'contact': admin.contact,
                    'image': admin.image,
                    'address': admin.adress,  # ✅ fixed typo: 'adress' from model
                    'zip_code': admin.zip_code,
                })

            return JsonResponse({'admins': data}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=405)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_admin(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            firstname = data.get('firstname')
            lastname = data.get('lastname')
            email = data.get('email')
            password = data.get('password')
            contact = data.get('contact')
            role = data.get('role', 'user')
            is_online = data.get('is_online', False)
            adress = data.get('adress')
            zip_code = data.get('zip_code')
            image = data.get('image')
            created_by_id = data.get('created_by')

            if not all([firstname, lastname, email, password, contact]):
                return JsonResponse({'error': 'Missing required fields.'}, status=400)

            user = User(
                firstname=firstname,
                lastname=lastname,
                email=email,
                contact=contact,
                password=password,
                role=role,
                adress=adress,
                zip_code=zip_code,
                image=image,
                is_online=is_online
            )

            if created_by_id:
                try:
                    creator = User.objects.get(user_id=created_by_id)
                    user.created_by = creator
                except User.DoesNotExist:
                    return JsonResponse({'error': 'Creator user not found.'}, status=404)

            user.save()

            return JsonResponse({
                'user_id': user.user_id,
                'firstname': user.firstname,
                'lastname': user.lastname,
                'email': user.email,
                'role': user.role,
                'message': 'User created successfully.'
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def fetching_user(request):
    user_id = request.GET.get('user_id')

    if user_id:
        try:
            user = User.objects.values(
                'user_id', 'firstname', 'lastname', 'email', 'contact', 
                'role', 'adress', 'zip_code', 'is_online', 'image', 'password'
            ).get(user_id=user_id)
            return JsonResponse(user, safe=False)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    else:
        users = User.objects.values(
            'user_id', 'firstname', 'lastname', 'email', 'contact', 
            'role', 'adress', 'zip_code', 'is_online', 'image', 'password'
        )
        return JsonResponse(list(users), safe=False)
    


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def assign_user_to_admin(request):
    try:
        data = json.loads(request.body)
        admin_id = data.get('admin_id')
        user_id = data.get('user_id')

        if not admin_id or not user_id:
            return JsonResponse({'error': 'admin_id and user_id are required.'}, status=400)

        admin = User.objects.get(user_id=admin_id, role='admin')
        user = User.objects.get(user_id=user_id)

        user.created_by = admin
        user.save()

        return JsonResponse({'message': f'User {user.firstname} assigned to Admin {admin.firstname}.'}, status=200)

    except User.DoesNotExist:
        return JsonResponse({'error': 'User or Admin not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_unassigned_users(request):
    users = User.objects.filter(created_by__isnull=True, role='user')
    user_list = [{
        'user_id': u.user_id,
        'firstname': u.firstname,
        'lastname': u.lastname,
        'email': u.email,
        'contact': u.contact,
        'role': u.role
    } for u in users]
    return JsonResponse({'unassigned_users': user_list}, safe=False)




@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_all_gateways(request):
    try:
        gateways = Gateways.objects.all()
        serializer = GatewaysSerializer(gateways, many=True)
        return Response({"success": True, "gateways": serializer.data})
    except Exception as e:
        return Response({"success": False, "error": str(e)})

