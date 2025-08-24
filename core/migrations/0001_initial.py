from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Component',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=32, unique=True, verbose_name='Código')),
                ('name', models.CharField(max_length=120, verbose_name='Nome')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('unit_cost', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Custo unitário (R$)')),
                ('print_time_min', models.PositiveIntegerField(default=0, verbose_name='Tempo de impressão (min/un)')),
                ('qty_on_hand', models.PositiveIntegerField(default=0, verbose_name='Qtd em estoque')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['code']},
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=32, unique=True, verbose_name='Código')),
                ('name', models.CharField(max_length=120, verbose_name='Nome')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('qty_on_hand', models.PositiveIntegerField(default=0, verbose_name='Qtd em estoque')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['code']},
        ),
        migrations.CreateModel(
            name='ProductionOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('status', models.CharField(choices=[('open','Aberta'),('done','Finalizada'),('cancelled','Cancelada')], default='open', max_length=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='core.product')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='BOMItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Qtd por produto')),
                ('component', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bom_items', to='core.component')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bom_items', to='core.product')),
            ],
        ),
        migrations.CreateModel(
            name='ProductionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('component', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.component')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='core.productionorder')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='bomitem',
            unique_together={('product','component')},
        ),
    ]
