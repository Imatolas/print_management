from django.db import migrations, models
import django.db.models.deletion
import django.core.validators

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_printer_component_base_time_min_component_batch_size_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrintTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('status', models.CharField(default='pending', max_length=20)),
                ('component', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.component')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='print_tasks', to='core.productionorder')),
                ('printer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.printer')),
            ],
        ),
    ]
