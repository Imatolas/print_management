from django.test import TestCase
from django.urls import reverse
from core.scheduling import (
    PrinterDTO,
    TaskDTO,
    schedule_tasks,
    expand_workorder_to_tasks,
)
from core.models import Component, Product, BOMItem, WorkOrder, Printer


class SchedulingServiceTests(TestCase):
    def test_lpt_two_printers(self):
        printers = [
            PrinterDTO(1, 'P1', 1.0, set()),
            PrinterDTO(2, 'P2', 1.0, set()),
        ]
        tasks = [
            TaskDTO(1, 'A', 1, 180, set()),
            TaskDTO(2, 'B', 1, 120, set()),
        ]
        assignments, unassigned, makespan, times = schedule_tasks(tasks, printers)
        self.assertEqual(round(makespan), 180)
        self.assertEqual(len(assignments), 2)
        self.assertEqual(len(unassigned), 0)

    def test_lpt_single_printer(self):
        printers = [PrinterDTO(1, 'P1', 1.0, set())]
        tasks = [
            TaskDTO(1, 'A', 1, 180, set()),
            TaskDTO(2, 'B', 1, 120, set()),
        ]
        assignments, unassigned, makespan, times = schedule_tasks(tasks, printers)
        self.assertEqual(round(makespan), 300)

    def test_speed_factor(self):
        printers = [PrinterDTO(1, 'P1', 2.0, set())]
        tasks = [TaskDTO(1, 'A', 1, 120, set())]
        assignments, unassigned, makespan, times = schedule_tasks(tasks, printers)
        self.assertAlmostEqual(makespan, 60)

    def test_tag_incompatibility(self):
        printers = [PrinterDTO(1, 'P1', 1.0, {'pla'})]
        tasks = [TaskDTO(1, 'A', 1, 60, {'abs'})]
        assignments, unassigned, makespan, times = schedule_tasks(tasks, printers)
        self.assertEqual(len(unassigned), 1)

    def test_expand_workorder_batch(self):
        comp = Component.objects.create(
            code='C1',
            name='Comp1',
            base_time_min=10,
            per_plate_time_min=60,
            batch_size=2,
        )
        prod = Product.objects.create(code='P1', name='Prod1')
        BOMItem.objects.create(product=prod, component=comp, quantity=3)
        wo = WorkOrder.objects.create(product=prod, quantity=1)
        tasks = expand_workorder_to_tasks(wo)
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].time_min, 70)
        self.assertEqual(tasks[1].time_min, 60)


class SchedulingAPITests(TestCase):
    def setUp(self):
        self.printer = Printer.objects.create(name='P1', is_active=True, speed_factor=1.0)
        self.component = Component.objects.create(
            code='C1',
            name='Comp',
            base_time_min=0,
            per_plate_time_min=60,
            batch_size=1,
        )
        self.product = Product.objects.create(code='PR1', name='Prod')
        BOMItem.objects.create(product=self.product, component=self.component, quantity=1)
        self.workorder = WorkOrder.objects.create(product=self.product, quantity=1)

    def test_schedule_endpoint(self):
        resp = self.client.post(
            '/api/schedule/',
            data={'workorder_id': self.workorder.id},
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['assignments']), 1)

    def test_toggle_printer(self):
        resp = self.client.patch(f'/api/printers/{self.printer.id}/toggle/')
        self.assertEqual(resp.status_code, 200)
        self.printer.refresh_from_db()
        self.assertFalse(self.printer.is_active)

    def test_preview_tasks(self):
        resp = self.client.get(f'/api/workorders/{self.workorder.id}/tasks/preview/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
