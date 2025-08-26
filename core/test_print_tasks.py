from django.test import TestCase
from django.core.exceptions import ValidationError
from core.models import (
    Component,
    Product,
    BOMItem,
    ProductionOrder,
    Printer,
    PrintTask,
)
from core.print_tasks import calculate_order_times


class PrintTaskCalculationTests(TestCase):
    def _setup_product(self):
        product = Product.objects.create(code="P1", name="Prod")
        return product

    def test_example1_single_component_parallel(self):
        product = self._setup_product()
        comp_a = Component.objects.create(code="A", name="CompA", print_time_min=12)
        BOMItem.objects.create(product=product, component=comp_a, quantity=50)
        order = ProductionOrder.objects.create(product=product, quantity=1)
        printers = [
            Printer.objects.create(name=f"P{i}", is_active=True, speed_factor=1.0)
            for i in range(5)
        ]
        for p in printers:
            PrintTask.objects.create(order=order, component=comp_a, printer=p, quantity=10)
        stats, total = calculate_order_times(order)
        self.assertAlmostEqual(total, 2.0)
        comp_stat = stats[0]
        self.assertEqual(comp_stat.assigned_qty, 50)
        self.assertAlmostEqual(comp_stat.capacity, 5.0)
        self.assertAlmostEqual(comp_stat.time_h, 2.0)
        self.assertEqual(comp_stat.remaining_qty, 0)

    def test_example2_two_components(self):
        product = self._setup_product()
        comp_a = Component.objects.create(code="A", name="CompA", print_time_min=12)
        comp_b = Component.objects.create(code="B", name="CompB", print_time_min=3)
        BOMItem.objects.create(product=product, component=comp_a, quantity=50)
        BOMItem.objects.create(product=product, component=comp_b, quantity=20)
        order = ProductionOrder.objects.create(product=product, quantity=1)
        printers_a = [
            Printer.objects.create(name=f"PA{i}", is_active=True, speed_factor=1.0)
            for i in range(5)
        ]
        printers_b = [
            Printer.objects.create(name=f"PB{i}", is_active=True, speed_factor=1.0)
            for i in range(5)
        ]
        for p in printers_a:
            PrintTask.objects.create(order=order, component=comp_a, printer=p, quantity=10)
        for p in printers_b:
            PrintTask.objects.create(order=order, component=comp_b, printer=p, quantity=4)
        stats, total = calculate_order_times(order)
        self.assertAlmostEqual(total, 2.0)
        stat_a = next(s for s in stats if s.component == comp_a)
        stat_b = next(s for s in stats if s.component == comp_b)
        self.assertAlmostEqual(stat_a.time_h, 2.0)
        self.assertAlmostEqual(stat_b.time_h, 0.2)

    def test_example3_partial_with_remaining(self):
        product = self._setup_product()
        comp_a = Component.objects.create(code="A", name="CompA", print_time_min=12)
        BOMItem.objects.create(product=product, component=comp_a, quantity=50)
        order = ProductionOrder.objects.create(product=product, quantity=1)
        printers = [
            Printer.objects.create(name=f"P{i}", is_active=True, speed_factor=1.0)
            for i in range(2)
        ]
        for p in printers:
            PrintTask.objects.create(order=order, component=comp_a, printer=p, quantity=10)
        stats, total = calculate_order_times(order)
        self.assertAlmostEqual(total, 2.0)
        comp_stat = stats[0]
        self.assertEqual(comp_stat.assigned_qty, 20)
        self.assertEqual(comp_stat.remaining_qty, 30)
        self.assertAlmostEqual(comp_stat.remaining_time_h, 6.0)

    def test_quantity_exceed_validation(self):
        product = self._setup_product()
        comp_a = Component.objects.create(code="A", name="CompA", print_time_min=12)
        BOMItem.objects.create(product=product, component=comp_a, quantity=50)
        order = ProductionOrder.objects.create(product=product, quantity=1)
        p1 = Printer.objects.create(name="P1", is_active=True, speed_factor=1.0)
        p2 = Printer.objects.create(name="P2", is_active=True, speed_factor=1.0)
        PrintTask.objects.create(order=order, component=comp_a, printer=p1, quantity=40)
        with self.assertRaises(ValidationError):
            PrintTask.objects.create(order=order, component=comp_a, printer=p2, quantity=20)

    def test_inactive_printer_validation(self):
        product = self._setup_product()
        comp_a = Component.objects.create(code="A", name="CompA", print_time_min=12)
        BOMItem.objects.create(product=product, component=comp_a, quantity=10)
        order = ProductionOrder.objects.create(product=product, quantity=1)
        printer = Printer.objects.create(name="PX", is_active=False, speed_factor=1.0)
        with self.assertRaises(ValidationError):
            PrintTask.objects.create(order=order, component=comp_a, printer=printer, quantity=5)
