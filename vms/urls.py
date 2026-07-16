from django.urls import path
from .views import (
    signup_view, login_view,refresh_token_view, create_role, update_parent,
    get_all_usertypes, get_all_users, delete_user,

    get_all_clients_for_superadmin, get_all_customers_for_superadmin,
    get_all_projects_for_superadmin, get_all_gateways_for_superadmin,
    reassign_clients_to_admin, reassign_customers_to_client,
    reassign_gateways_to_customer, reassign_gateways_to_project,
    reassign_projects_to_client,

    admin_details_view, admin_clients, admin_client_customers,
    admin_projects, admin_project_gateways, all_admin_customers,
    all_admin_gateways, admin_available_gateways,

    client_my_customers, client_my_projects, client_project_gateways,
    create_customer, update_customer, client_customers_list,

    customer_my_gateways, customer_gateway_detail,

    create_project, update_project, delete_project,

    create_gateway, update_gateway, delete_gateway,
    assign_gateway_to_user, get_gateway_types, create_gateway_type,
    receive_gateway_data, check_gateway_status,

    create_sensor, create_camera,
    update_device_status,
    receive_metadata,
    update_client,
    run_system_checks,
    get_gateway_sensors,
    get_sensor_by_id,
     firebase_login_view,
     client_all_gateways

   
)

app_name = 'vms'

urlpatterns = [

    # --- Auth & General ---
    path('auth/general/signup/',                    signup_view,         name='signup'),
    path('auth/general/login/',                     login_view,          name='login'),
    path('auth/general/token/refresh/', refresh_token_view, name='token_refresh'),
    path('roles/general/create/',                   create_role,         name='create_role'),
    path('users/general/update-parent/',            update_parent,       name='update_parent'),
    path('users/general/all/',                      get_all_users,       name='all_users'),
    path('usertypes/general/',                      get_all_usertypes,   name='usertypes'),
    path('users/general/delete/<int:user_id>/',     delete_user,         name='delete_user'),

    # --- Superadmin ---
    path('superadmin/general/clients/',                          get_all_clients_for_superadmin,    name='superadmin_clients'),
    path('superadmin/general/customers/',                        get_all_customers_for_superadmin,  name='superadmin_customers'),
    path('superadmin/general/projects/',                         get_all_projects_for_superadmin,   name='superadmin_projects'),
    path('superadmin/general/gateways/',                         get_all_gateways_for_superadmin,   name='superadmin_gateways'),
    path('superadmin/general/reassign-clients/',                 reassign_clients_to_admin,         name='superadmin_reassign_clients'),
    path('superadmin/general/reassign-customers/',               reassign_customers_to_client,      name='superadmin_reassign_customers'),
    path('superadmin/general/reassign-projects/',                reassign_projects_to_client,       name='superadmin_reassign_projects'),
    path('superadmin/general/reassign-gateways-to-customer/',    reassign_gateways_to_customer,     name='superadmin_reassign_gateways_customer'),
    path('superadmin/general/reassign-gateways-to-project/',     reassign_gateways_to_project,      name='superadmin_reassign_gateways_project'),

    # --- Admin ---
    path('admin/general/details/',                                  admin_details_view,       name='admin_details'),
    path('admin/general/clients/<int:admin_id>/',                   admin_clients,            name='admin_clients'),
    path('admin/general/customers/<int:admin_id>/',                 all_admin_customers,      name='admin_customers'),
    path('admin/general/projects/<int:admin_id>/',                  admin_projects,           name='admin_projects'),
    path('admin/general/gateways/<int:admin_id>/',                  all_admin_gateways,       name='admin_gateways'),
    path('admin/general/available-gateways/<int:client_id>/',       admin_available_gateways, name='admin_available_gateways'),
    path('admin/general/client-customers/<int:client_id>/',         admin_client_customers,   name='admin_client_customers'),
    path('admin/general/project-gateways/<int:project_id>/',        admin_project_gateways,   name='admin_project_gateways'),

    # --- Client ---
    path('client/general/customers/<int:client_id>/',                           client_my_customers,     name='client_customers'),
    path('client/general/projects/<int:client_id>/',                            client_my_projects,      name='client_projects'),
    path('client/general/project-gateways/<int:client_id>/<int:project_id>/',   client_project_gateways, name='client_project_gateways'),
    path('client/general/create-customer/', create_customer, name='create_customer'),    
    path('client/general/customers/update/<int:customer_id>/',                   update_customer,         name='update_customer'),
    path('clients/general/update/<int:client_id>/', update_client, name='update_client'),
    path('client/general/gateways/<int:client_id>/', client_all_gateways, name='client_gateways'),



    # --- Customer ---
    path('customer/general/gateways/<int:customer_id>/',                         customer_my_gateways,    name='customer_gateways'),
    path('customer/general/gateway-detail/<int:customer_id>/<int:gateway_id>/',  customer_gateway_detail, name='customer_gateway_detail'),

    # --- Projects ---
    path('projects/general/create/',                    create_project,  name='create_project'),
    path('projects/general/update/<int:project_id>/',   update_project,  name='update_project'),
    path('projects/general/delete/<int:project_id>/',   delete_project,  name='delete_project'),

    # --- Gateways ---
    path('gateways/general/create/',                        create_gateway,         name='create_gateway'),
    path('gateways/general/update/<int:gateway_id>/',       update_gateway,         name='update_gateway'),
    path('gateways/general/delete/<int:gateway_id>/',       delete_gateway,         name='delete_gateway'),
    path('gateways/general/assign/',                        assign_gateway_to_user, name='assign_gateway'),
    path('gateways/general/types/',                         get_gateway_types,      name='gateway_types'),
    path('gateways/general/create-type/',                   create_gateway_type,    name='create_gateway_type'),
    path('gateways/general/receive-data/',                  receive_gateway_data,   name='receive_gateway_data'),
    path('gateways/general/check-status/',                  check_gateway_status,   name='check_gateway_status'),
    path('gateways/general/receive_metadata/', receive_metadata, name='receive-metadata'),



    # --- Sensors & Cameras ---
    path('sensors/general/create/',  create_sensor,  name='create_sensor'),
    path('cameras/general/create/',  create_camera,  name='create_camera'),
    path('devices/general/update-status/', update_device_status, name='update_device_status'),
    path('sensors/general/<int:sensor_id>/', get_sensor_by_id, name='get_sensor_by_id'),
    



]

# ---------------------------------------------------------------------------
# New structured API aliases - added as a non-breaking migration layer.
# Old endpoints above stay active while frontend/mobile/gateway clients move
# gradually to these clearer /general, /webapps, /mobileapps, /gateways groups.
# ---------------------------------------------------------------------------

urlpatterns += [
    # --- General / Auth: shared auth endpoints for web, mobile, and tooling ---
    path('general/auth/signup/', signup_view, name='v1_general_auth_signup'),
    path('general/auth/login/', login_view, name='v1_general_auth_login'),
    path('general/auth/token/refresh/', refresh_token_view, name='v1_general_auth_token_refresh'),

    # --- General / Users & roles: common CRM/ERP identity lookups and actions ---
    path('general/roles/', create_role, name='v1_general_roles_create'),
    path('general/users/', get_all_users, name='v1_general_users_list'),
    path('general/users/update-parent/', update_parent, name='v1_general_users_update_parent'),
    path('general/users/<int:user_id>/', delete_user, name='v1_general_users_delete'),
    path('general/user-types/', get_all_usertypes, name='v1_general_user_types'),

    # --- General / Lookups: shared gateway type/subtype catalog ---
    path('general/gateway-types/', get_gateway_types, name='v1_general_gateway_types'),

    # --- General / Scheduled checks: Cloud Scheduler entrypoint for stale gateway, invoice, and project-control checks ---
    path('general/system-checks/run/', run_system_checks, name='v1_general_system_checks_run'),

    # --- Webapps / Superadmin: CRM/ERP global management screens ---
    path('webapps/superadmin/clients/', get_all_clients_for_superadmin, name='v1_webapps_superadmin_clients'),
    path('webapps/superadmin/customers/', get_all_customers_for_superadmin, name='v1_webapps_superadmin_customers'),
    path('webapps/superadmin/projects/', get_all_projects_for_superadmin, name='v1_webapps_superadmin_projects'),
    path('webapps/superadmin/gateways/', get_all_gateways_for_superadmin, name='v1_webapps_superadmin_gateways'),

    # --- Webapps / Superadmin reassignments: ownership transfer workflows ---
    path('webapps/superadmin/reassign/clients/', reassign_clients_to_admin, name='v1_webapps_superadmin_reassign_clients'),
    path('webapps/superadmin/reassign/customers/', reassign_customers_to_client, name='v1_webapps_superadmin_reassign_customers'),
    path('webapps/superadmin/reassign/projects/', reassign_projects_to_client, name='v1_webapps_superadmin_reassign_projects'),
    path('webapps/superadmin/reassign/gateways/customer/', reassign_gateways_to_customer, name='v1_webapps_superadmin_reassign_gateways_customer'),
    path('webapps/superadmin/reassign/gateways/project/', reassign_gateways_to_project, name='v1_webapps_superadmin_reassign_gateways_project'),

    # --- Webapps / Admins: admin dashboard list and drilldown screens ---
    path('webapps/admins/', admin_details_view, name='v1_webapps_admins'),
    path('webapps/admins/<int:admin_id>/clients/', admin_clients, name='v1_webapps_admin_clients'),
    path('webapps/admins/<int:admin_id>/customers/', all_admin_customers, name='v1_webapps_admin_customers'),
    path('webapps/admins/<int:admin_id>/projects/', admin_projects, name='v1_webapps_admin_projects'),
    path('webapps/admins/<int:admin_id>/gateways/', all_admin_gateways, name='v1_webapps_admin_gateways'),

    # --- Webapps / Admin client drilldowns: customers and warehouse assignment views ---
    path('webapps/admin-clients/<int:client_id>/customers/', admin_client_customers, name='v1_webapps_admin_client_customers'),
    path('webapps/admin-clients/<int:client_id>/available-gateways/', admin_available_gateways, name='v1_webapps_admin_client_available_gateways'),

    # --- Webapps / Clients: client dashboard, customer CRUD, and project gateway views ---
    path('webapps/clients/<int:client_id>/', update_client, name='v1_webapps_clients_update'),
    path('webapps/clients/<int:client_id>/customers/', client_my_customers, name='v1_webapps_client_customers'),
    path('webapps/clients/<int:client_id>/projects/', client_my_projects, name='v1_webapps_client_projects'),
    path('webapps/clients/<int:client_id>/projects/<int:project_id>/gateways/', client_project_gateways, name='v1_webapps_client_project_gateways'),
    path('webapps/clients/customers/', create_customer, name='v1_webapps_client_customers_create'),
    path('webapps/customers/<int:customer_id>/', update_customer, name='v1_webapps_customers_update'),

    # --- Webapps / Customers: customer dashboard gateway list and gateway detail ---
    path('webapps/customers/<int:customer_id>/gateways/', customer_my_gateways, name='v1_webapps_customer_gateways'),
    path('webapps/customers/<int:customer_id>/gateways/<int:gateway_id>/', customer_gateway_detail, name='v1_webapps_customer_gateway_detail'),

    # --- Webapps / Projects: CRM/ERP project CRUD ---
    path('webapps/projects/', create_project, name='v1_webapps_projects_create'),
    path('webapps/projects/<int:project_id>/', update_project, name='v1_webapps_projects_update'),
    path('webapps/projects/<int:project_id>/delete/', delete_project, name='v1_webapps_projects_delete'),
    path('webapps/projects/<int:project_id>/gateways/', admin_project_gateways, name='v1_webapps_project_gateways'),

    # --- Webapps / Gateway management: dashboard-side gateway CRUD and assignment ---
    path('webapps/gateways/', create_gateway, name='v1_webapps_gateways_create'),
    path('webapps/gateways/<int:gateway_id>/', update_gateway, name='v1_webapps_gateways_update'),
    path('webapps/gateways/<int:gateway_id>/delete/', delete_gateway, name='v1_webapps_gateways_delete'),
    path('webapps/gateways/assign/', assign_gateway_to_user, name='v1_webapps_gateways_assign'),
    path('webapps/gateways/types/create/', create_gateway_type, name='v1_webapps_gateway_types_create'),

    # --- Webapps / Devices: dashboard-side sensor, camera, and device status actions ---
    path('webapps/sensors/', create_sensor, name='v1_webapps_sensors_create'),
    path('webapps/cameras/', create_camera, name='v1_webapps_cameras_create'),
    path('webapps/devices/status/', update_device_status, name='v1_webapps_devices_status_update'),

    # --- Mobileapps / Auth: mobile login aliases, same auth logic for now ---
    path('mobileapps/auth/login/', login_view, name='v1_mobileapps_auth_login'),
    path('mobileapps/auth/token/refresh/', refresh_token_view, name='v1_mobileapps_auth_token_refresh'),

    # --- Mobileapps / Customer gateways: mobile-friendly user gateway reads ---
    path('mobileapps/users/<int:customer_id>/gateways/', customer_my_gateways, name='v1_mobileapps_user_gateways'),
    path('mobileapps/users/<int:customer_id>/gateways/<int:gateway_id>/', customer_gateway_detail, name='v1_mobileapps_user_gateway_detail'),

    # --- Gateway devices / Hits: physical gateway JSON heartbeat and telemetry ingest ---
    path('gateways/hits/', receive_gateway_data, name='v1_gateways_hits'),
    path('gateways/metadata/', receive_metadata, name='v1_gateways_metadata'),
    path('gateways/status/check/', check_gateway_status, name='v1_gateways_status_check'),

    path('mobileapps/sensors/<int:gateway_id>/',get_gateway_sensors,name='get_gateway_sensors'),
path('auth/general/firebase-login/', firebase_login_view, name='firebase_login'),
]
