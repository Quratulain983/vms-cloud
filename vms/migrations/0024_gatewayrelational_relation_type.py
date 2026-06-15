from django.db import migrations, models


def backfill_relation_type(apps, schema_editor):
    GatewayRelational = apps.get_model('vms', 'GatewayRelational')

    for relation in GatewayRelational.objects.select_related('user__usertype'):
        usertype_name = ''
        if relation.user and relation.user.usertype:
            usertype_name = (relation.user.usertype.name or '').strip().lower()

        relation.relation_type = 'client' if usertype_name == 'client' else 'customer'
        relation.save(update_fields=['relation_type'])


class Migration(migrations.Migration):

    dependencies = [
        ('vms', '0023_metadata_gateway_hit_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='gatewayrelational',
            name='relation_type',
            field=models.CharField(
                choices=[('client', 'Client'), ('customer', 'Customer')],
                default='customer',
                max_length=20,
            ),
        ),
        migrations.RunPython(backfill_relation_type, migrations.RunPython.noop),
    ]
