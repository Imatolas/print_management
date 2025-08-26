from django.test import TestCase
from core.models import Product, Component, BOMItem, ProductionOrder, ProductionLog


class ProductionOrderTimeTests(TestCase):
    def test_time_remaining_aggregates_components(self):
        product = Product.objects.create(code="P1", name="Prod")
        comp_a = Component.objects.create(code="C1", name="CompA", print_time_min=60)
        comp_b = Component.objects.create(code="C2", name="CompB", print_time_min=30)
        BOMItem.objects.create(product=product, component=comp_a, quantity=2)
        BOMItem.objects.create(product=product, component=comp_b, quantity=1)
        order = ProductionOrder.objects.create(product=product, quantity=1)
        self.assertEqual(order.time_remaining_minutes(), 120)
        self.assertEqual(order.time_remaining_hhmm, "2h00")
        ProductionLog.objects.create(order=order, component=comp_a, quantity=1)
        self.assertEqual(order.time_remaining_minutes(), 60)
        self.assertEqual(order.time_remaining_hhmm, "1h00")
