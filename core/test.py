from django.test import TestCase
from django.urls import reverse
from .models import Component, Product, BOMItem, ProductionOrder


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

    def test_create_product_with_components(self):
        comp = Component.objects.create(code="C1", name="Comp", unit_cost=5)
        data = {
            "code": "P1",
            "name": "Prod",
            "description": "",
            "qty_on_hand": "0",
            "bom_items-TOTAL_FORMS": "1",
            "bom_items-INITIAL_FORMS": "0",
            "bom_items-MIN_NUM_FORMS": "0",
            "bom_items-MAX_NUM_FORMS": "1000",
            "bom_items-0-id": "",
            "bom_items-0-component": str(comp.pk),
            "bom_items-0-quantity": "6",
        }
        response = self.client.post(reverse("produtos-new"), data)
        self.assertRedirects(response, reverse("estoque-produtos"))
        prod = Product.objects.get(code="P1")
        self.assertEqual(prod.bom_items.count(), 1)
        self.assertEqual(prod.total_cost, 30)

    def test_create_product_with_multiple_components(self):
        c1 = Component.objects.create(code="C1", name="C1", unit_cost=5)
        c2 = Component.objects.create(code="C2", name="C2", unit_cost=4)
        data = {
            "code": "P2",
            "name": "Prod2",
            "description": "",
            "qty_on_hand": "0",
            "bom_items-TOTAL_FORMS": "2",
            "bom_items-INITIAL_FORMS": "0",
            "bom_items-MIN_NUM_FORMS": "0",
            "bom_items-MAX_NUM_FORMS": "1000",
            "bom_items-0-id": "",
            "bom_items-0-component": str(c1.pk),
            "bom_items-0-quantity": "2",
            "bom_items-1-id": "",
            "bom_items-1-component": str(c2.pk),
            "bom_items-1-quantity": "3",
        }
        response = self.client.post(reverse("produtos-new"), data)
        self.assertRedirects(response, reverse("estoque-produtos"))
        prod = Product.objects.get(code="P2")
        self.assertEqual(prod.bom_items.count(), 2)
        self.assertEqual(prod.total_cost, 22)

    def test_edit_product_add_component(self):
        comp = Component.objects.create(code="C1", name="Comp", unit_cost=5)
        prod = Product.objects.create(code="P1", name="Prod")
        url = reverse("produtos-edit", args=[prod.pk])
        data = {
            "code": prod.code,
            "name": prod.name,
            "description": "",
            "qty_on_hand": "0",
            "bom_items-TOTAL_FORMS": "1",
            "bom_items-INITIAL_FORMS": "0",
            "bom_items-MIN_NUM_FORMS": "0",
            "bom_items-MAX_NUM_FORMS": "1000",
            "bom_items-0-id": "",
            "bom_items-0-component": str(comp.pk),
            "bom_items-0-quantity": "6",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("estoque-produtos"))
        prod.refresh_from_db()
        self.assertEqual(prod.bom_items.count(), 1)
        self.assertEqual(prod.total_cost, 30)


class ProductionOrderTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(code="P1", name="Prod")

    def test_production_list_page(self):
        response = self.client.get(reverse("producao"))
        self.assertEqual(response.status_code, 200)

    def test_edit_production_order(self):
        order = ProductionOrder.objects.create(product=self.product, quantity=5)
        url = reverse("producao-edit", args=[order.pk])
        data = {
            "product": self.product.pk,
            "quantity": 10,
            "due_date": "",
            "notes": "",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("producao"))
        order.refresh_from_db()
        self.assertEqual(order.quantity, 10)

    def test_delete_production_order(self):
        order = ProductionOrder.objects.create(product=self.product, quantity=5)
        url = reverse("producao-delete", args=[order.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("producao"))
        self.assertFalse(ProductionOrder.objects.filter(pk=order.pk).exists())


class ProductionLogAPITests(TestCase):
    def test_create_log(self):
        comp = Component.objects.create(code="C1", name="Comp")
        prod = Product.objects.create(code="P1", name="Prod")
        BOMItem.objects.create(product=prod, component=comp, quantity=5)
        order = ProductionOrder.objects.create(product=prod, quantity=1)
        url = reverse("api-log-create")
        data = {"order_id": order.id, "component_id": comp.id, "quantity": 2}
        response = self.client.post(url, data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        from .models import ProductionLog

        self.assertEqual(ProductionLog.objects.count(), 1)
        log = ProductionLog.objects.first()
        self.assertEqual(log.order, order)
        self.assertEqual(log.component, comp)
        self.assertEqual(log.quantity, 2)
