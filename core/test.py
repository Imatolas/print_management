from django.test import TestCase
from django.urls import reverse
from .models import Component, Product, BOMItem

class SmokeTests(TestCase):
    def test_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


class ProductBOMTests(TestCase):
    def test_total_cost_with_components(self):
        comp = Component.objects.create(code="C1", name="Comp", unit_cost=10)
        prod = Product.objects.create(code="P1", name="Prod")
        BOMItem.objects.create(product=prod, component=comp, quantity=6)
        self.assertEqual(prod.total_cost, 60)

    def test_add_component_via_view(self):
        comp = Component.objects.create(code="C1", name="Comp", unit_cost=5)
        prod = Product.objects.create(code="P1", name="Prod")
        url = reverse("produtos-bom", args=[prod.pk])
        data = {
            "code": prod.code,
            "name": prod.name,
            "description": "",
            "qty_on_hand": "0",
            "bom_items-TOTAL_FORMS": "1",
            "bom_items-INITIAL_FORMS": "0",
            "bom_items-MIN_NUM_FORMS": "0",
            "bom_items-MAX_NUM_FORMS": "1000",
            "bom_items-0-component": str(comp.pk),
            "bom_items-0-quantity": "6",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("estoque-produtos"))
        self.assertEqual(prod.bom_items.count(), 1)
        self.assertEqual(prod.total_cost, 30)
