# Generated manually because Django is not installed in the active environment.

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


DEPLOY_STATUSES = [
    ("deploy_to_warehouse", "Deploy to Warehouse", "Gateway is registered and kept in warehouse."),
    ("assign_to_client", "Assign to Client", "Gateway is allotted to a client."),
    ("assign_to_customer", "Assign to Customer", "Gateway is allotted to a customer."),
]

ACTIVE_STATUSES = [
    ("connected_no_data_found", "Gateway connected no data found", "Gateway hit the server but no metadata payload was found."),
    ("connected_wrong_data_found", "Gateway connected wrong data found", "Gateway hit the server but metadata payload was invalid."),
    ("connected_data_found", "Gateway connected data found", "Gateway hit the server with valid metadata payload."),
    ("not_connected", "Gateway not connected", "Gateway has not hit the server or is past the allowed heartbeat window."),
]


def seed_gateway_statuses(apps, schema_editor):
    GatewayDeployStatus = apps.get_model("vms", "GatewayDeployStatus")
    GatewayActiveStatus = apps.get_model("vms", "GatewayActiveStatus")
    Gateway = apps.get_model("vms", "Gateway")

    deploy_objects = {}
    for name, label, description in DEPLOY_STATUSES:
        obj, _ = GatewayDeployStatus.objects.get_or_create(
            name=name,
            defaults={"label": label, "description": description},
        )
        deploy_objects[name] = obj

    active_objects = {}
    for name, label, description in ACTIVE_STATUSES:
        obj, _ = GatewayActiveStatus.objects.get_or_create(
            name=name,
            defaults={"label": label, "description": description},
        )
        active_objects[name] = obj

    Gateway.objects.filter(deploy_status__isnull=True).update(
        deploy_status=deploy_objects["deploy_to_warehouse"]
    )
    Gateway.objects.filter(active_status__isnull=True).update(
        active_status=active_objects["not_connected"]
    )


def unseed_gateway_statuses(apps, schema_editor):
    GatewayDeployStatus = apps.get_model("vms", "GatewayDeployStatus")
    GatewayActiveStatus = apps.get_model("vms", "GatewayActiveStatus")

    GatewayDeployStatus.objects.filter(name__in=[name for name, _, _ in DEPLOY_STATUSES]).delete()
    GatewayActiveStatus.objects.filter(name__in=[name for name, _, _ in ACTIVE_STATUSES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("vms", "0020_gatewaystatustype_remove_gateway_active_status_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="GatewayActiveStatus",
            fields=[
                ("active_status_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=50, unique=True)),
                ("label", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True, null=True)),
            ],
            options={
                "db_table": "gateway_active_status",
            },
        ),
        migrations.CreateModel(
            name="GatewayDeployStatus",
            fields=[
                ("deploy_status_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=50, unique=True)),
                ("label", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True, null=True)),
            ],
            options={
                "db_table": "gateway_deploy_status",
            },
        ),
        migrations.AddField(
            model_name="gateway",
            name="active_status",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="gateways",
                to="vms.gatewayactivestatus",
            ),
        ),
        migrations.AddField(
            model_name="gateway",
            name="deploy_status",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="gateways",
                to="vms.gatewaydeploystatus",
            ),
        ),
        migrations.AddField(
            model_name="gatewayrelational",
            name="active_status",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="gatewayrelational",
            name="assigned_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="gatewayrelational",
            name="last_hit_timestamp",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="gatewaystatus",
            name="deployment_status",
            field=models.CharField(
                choices=[
                    ("deploy_to_warehouse", "Deploy to Warehouse"),
                    ("assign_to_client", "Assign to Client"),
                    ("assign_to_customer", "Assign to Customer"),
                    ("added_to_warehouse", "Added to Warehouse"),
                    ("allotted_to_client", "Allotted to Client"),
                    ("allotted_to_customer", "Allotted to Customer"),
                    ("deployed_to_customer", "Deployed to Customer"),
                    ("active_to_customer", "Active to Customer"),
                ],
                default="deploy_to_warehouse",
                max_length=30,
            ),
        ),
        migrations.RunPython(seed_gateway_statuses, unseed_gateway_statuses),
        migrations.AlterField(
            model_name="gatewayrelational",
            name="assigned_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
