from django.test import TestCase
from django.urls import reverse
from .models import Component, Product, BOMItem, ProductionOrder, ProductionLog

class LogPrintAPITests(TestCase):
    def test_log_print_deducts_inventory(self):
        comp = Component.objects.create(code="C1", name="Comp", qty_on_hand=10, print_time_min=5)
        prod = Product.objects.create(code="P1", name="Prod")
        BOMItem.objects.create(product=prod, component=comp, quantity=5)
        order = ProductionOrder.objects.create(product=prod, quantity=1)
        url = reverse('api-log-print')
        response = self.client.post(url, data={
            'order_id': order.id,
            'component_id': comp.id,
            'quantity': 3,
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        comp.refresh_from_db()
        self.assertEqual(comp.qty_on_hand, 7)
        self.assertEqual(ProductionLog.objects.filter(order=order, component=comp, quantity=3).count(), 1)
