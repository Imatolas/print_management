from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.core.validators import MinValueValidator


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_component_material_production_time"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductionOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])),
                (
                    "status",
                    models.CharField(
                        choices=[("open", "Aberta"), ("done", "Finalizada"), ("cancelled", "Cancelada")],
                        default="open",
                        max_length=12,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="orders",
                        to="core.product",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ProductionLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "component",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.component"),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="logs",
                        to="core.productionorder",
                    ),
                ),
            ],
        ),
    ]
