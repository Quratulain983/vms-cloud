# Generated manually to store important gateway hit keys alongside raw JSON.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vms", "0022_gateway_subtype_series"),
    ]

    operations = [
        migrations.AddField(
            model_name="metadata",
            name="posted_timestamp",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="metadata",
            name="source_user_id",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="metadata",
            name="device_battery",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="metadata",
            name="sensors_alert",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="metadata",
            name="cam_alert",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="metadata",
            name="sensors_alert_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="metadata",
            name="cam_alert_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="metadata",
            name="location",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="metadata",
            name="phones",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="metadata",
            name="sensors_alert_events",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="metadata",
            name="cam_alert_events",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
