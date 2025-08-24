from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from .models import Printer, WorkOrder, minutes_to_hhmm
from .scheduling import (
    load_printers_active,
    expand_workorder_to_tasks,
    schedule_tasks,
)

# tentativa de usar DRF se disponível
try:
    from rest_framework.views import APIView as DRFAPIView
    from rest_framework.response import Response as DRFResponse

    class APIView(DRFAPIView):
        pass

    def Response(data, status=200):
        return DRFResponse(data, status=status)
except Exception:  # pragma: no cover
    class APIView(View):
        def dispatch(self, request, *args, **kwargs):
            return super().dispatch(request, *args, **kwargs)

    def Response(data, status=200):
        return JsonResponse(data, status=status, safe=False)


class PrinterListAPIView(APIView):
    def get(self, request):
        data = [
            {
                "id": p.id,
                "name": p.name,
                "is_active": p.is_active,
                "speed_factor": p.speed_factor,
                "tags": p.tags,
            }
            for p in Printer.objects.all()
        ]
        return Response(data)


class PrinterToggleAPIView(APIView):
    def patch(self, request, pk):
        printer = get_object_or_404(Printer, pk=pk)
        printer.is_active = not printer.is_active
        printer.save()
        return Response({"id": printer.id, "is_active": printer.is_active})


class ScheduleAPIView(APIView):
    def post(self, request):
        data = getattr(request, 'data', None)
        if data is None:
            try:
                import json
                data = json.loads(request.body.decode() or '{}')
            except Exception:
                data = {}
        workorder_id = data.get("workorder_id")
        workorder = get_object_or_404(WorkOrder, pk=workorder_id)
        tasks = expand_workorder_to_tasks(workorder)
        printers = load_printers_active()
        assignments, unassigned, makespan, printer_times = schedule_tasks(tasks, printers)
        resp = {
            "assignments": [
                {
                    "printer_id": a.printer_id,
                    "printer_name": next(p.name for p in printers if p.id == a.printer_id),
                    "component_id": a.task.component_id,
                    "component_name": a.task.component_name,
                    "quantity": a.task.quantity,
                    "start": a.start,
                    "end": a.end,
                    "duration": a.end - a.start,
                }
                for a in assignments
            ],
            "unassigned": [
                {
                    "component_id": t.component_id,
                    "component_name": t.component_name,
                    "quantity": t.quantity,
                    "time_min": t.time_min,
                }
                for t in unassigned
            ],
            "makespan_min": makespan,
            "makespan_hhmm": minutes_to_hhmm(makespan),
            "printer_times": printer_times,
        }
        return Response(resp)


class WorkOrderTasksPreviewAPIView(APIView):
    def get(self, request, pk):
        workorder = get_object_or_404(WorkOrder, pk=pk)
        tasks = expand_workorder_to_tasks(workorder)
        data = [
            {
                "component_id": t.component_id,
                "component_name": t.component_name,
                "quantity": t.quantity,
                "time_min": t.time_min,
            }
            for t in tasks
        ]
        return Response(data)
