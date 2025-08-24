from django.core.management.base import BaseCommand
from core.models import (
    Printer,
    Component,
    Product,
    BOMItem,
    WorkOrder,
)


class Command(BaseCommand):
    help = "Seed demo data for 3D print scheduling"

    def handle(self, *args, **options):
        p1, _ = Printer.objects.get_or_create(
            name="Bambu P1S",
            defaults={"speed_factor": 1.0, "tags": "bambu,pla"},
        )
        p2, _ = Printer.objects.get_or_create(
            name="Bambu A1",
            defaults={"speed_factor": 0.8, "tags": "bambu"},
        )
        p3, _ = Printer.objects.get_or_create(
            name="K1Max",
            defaults={"speed_factor": 1.2, "tags": "klipper,abs"},
        )

        c1, _ = Component.objects.get_or_create(
            code="CBASE",
            defaults={
                "name": "Base",
                "print_time_min": 0,
                "base_time_min": 10,
                "per_plate_time_min": 60,
                "batch_size": 4,
                "tags_required": "bambu",
            },
        )
        c2, _ = Component.objects.get_or_create(
            code="CTAMPA",
            defaults={
                "name": "Tampa",
                "print_time_min": 0,
                "base_time_min": 5,
                "per_plate_time_min": 40,
                "batch_size": 2,
                "tags_required": "klipper",
            },
        )

        prod, _ = Product.objects.get_or_create(code="PRD1", defaults={"name": "Produto Demo"})
        BOMItem.objects.get_or_create(product=prod, component=c1, defaults={"quantity": 1})
        BOMItem.objects.get_or_create(product=prod, component=c2, defaults={"quantity": 1})

        WorkOrder.objects.get_or_create(product=prod, quantity=5, defaults={"priority": 1})
        self.stdout.write(self.style.SUCCESS("Demo data created."))
