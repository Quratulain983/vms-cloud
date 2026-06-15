# Generated manually to normalize gateway major type and subtype.

import django.db.models.deletion
from django.db import migrations, models


def seed_gateway_series(apps, schema_editor):
    GatewayType = apps.get_model("vms", "GatewayType")
    GatewaySubType = apps.get_model("vms", "GatewaySubType")
    Gateway = apps.get_model("vms", "Gateway")

    mc, _ = GatewayType.objects.update_or_create(
        name="MC",
        defaults={"description": "Camera-capable gateway series. May include AI cameras."},
    )
    ms, _ = GatewayType.objects.update_or_create(
        name="MS",
        defaults={"description": "Sensor-only gateway series without camera streaming."},
    )

    subtypes = {}
    for parent, names in [(mc, ("MC1", "MC2")), (ms, ("MS1", "MS2"))]:
        for name in names:
            subtypes[name], _ = GatewaySubType.objects.update_or_create(
                gatewaytype=parent,
                name=name,
                defaults={"description": f"{name} gateway subtype"},
            )

    for gateway in Gateway.objects.select_related("gatewaytype").all():
        current_name = gateway.gatewaytype.name if gateway.gatewaytype else ""
        if current_name in ("MC", "MC Series") or "MC" in current_name.upper():
            gateway.gatewaytype = mc
            gateway.gatewaysubtype = subtypes["MC1"]
        else:
            gateway.gatewaytype = ms
            gateway.gatewaysubtype = subtypes["MS1"]
        gateway.save(update_fields=["gatewaytype", "gatewaysubtype"])

    GatewayType.objects.exclude(name__in=["MC", "MS"]).filter(gateways__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("vms", "0021_gateway_deploy_active_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="GatewaySubType",
            fields=[
                ("gatewaysubtype_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "gatewaytype",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subtypes",
                        to="vms.gatewaytype",
                    ),
                ),
            ],
            options={
                "db_table": "gatewaysubtype",
                "unique_together": {("gatewaytype", "name")},
            },
        ),
        migrations.AddField(
            model_name="gateway",
            name="gatewaysubtype",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="gateways",
                to="vms.gatewaysubtype",
            ),
        ),
        migrations.RunPython(seed_gateway_series, migrations.RunPython.noop),
    ]
