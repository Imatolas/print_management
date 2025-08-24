from dataclasses import dataclass
from typing import List, Set, Tuple, Dict
import math
from .models import Printer, WorkOrder, minutes_to_hhmm


# ======== DTOs ========
@dataclass
class PrinterDTO:
    id: int
    name: str
    speed_factor: float
    tags: Set[str]


@dataclass
class TaskDTO:
    component_id: int
    component_name: str
    quantity: int
    time_min: int
    tags_required: Set[str]


@dataclass
class AssignmentDTO:
    printer_id: int
    task: TaskDTO
    start: float
    end: float


# ======== Helpers ========
def parse_tags(value) -> Set[str]:
    if not value:
        return set()
    if isinstance(value, (list, set, tuple)):
        return {str(v).strip() for v in value if str(v).strip()}
    return {t.strip() for t in str(value).split(',') if t.strip()}


def is_printer_compatible(printer: PrinterDTO, task: TaskDTO) -> bool:
    return task.tags_required.issubset(printer.tags)


def expand_workorder_to_tasks(workorder: WorkOrder) -> List[TaskDTO]:
    tasks: List[TaskDTO] = []
    for bom in workorder.product.bom_items.select_related('component'):
        comp = bom.component
        total_qty = bom.quantity * workorder.quantity
        if comp.batch_size <= 0:
            plates = total_qty
            batch = 1
        else:
            plates = math.ceil(total_qty / comp.batch_size)
            batch = comp.batch_size
        remaining = total_qty
        first = True
        for _ in range(plates):
            qty = min(batch, remaining)
            duration = comp.per_plate_time_min
            if first:
                duration += comp.base_time_min
                first = False
            task = TaskDTO(
                component_id=comp.id,
                component_name=comp.name,
                quantity=qty,
                time_min=duration,
                tags_required=parse_tags(comp.tags_required),
            )
            tasks.append(task)
            remaining -= qty
    return tasks


def load_printers_active() -> List[PrinterDTO]:
    printers = []
    for p in Printer.objects.filter(is_active=True):
        printers.append(
            PrinterDTO(
                id=p.id,
                name=p.name,
                speed_factor=p.speed_factor or 1.0,
                tags=parse_tags(p.tags),
            )
        )
    return printers


def schedule_tasks(tasks: List[TaskDTO], printers: List[PrinterDTO]) -> Tuple[List[AssignmentDTO], List[TaskDTO], float, Dict[int, float]]:
    assignments: List[AssignmentDTO] = []
    unassigned: List[TaskDTO] = []
    if not printers:
        unassigned = list(tasks)
        return assignments, unassigned, 0.0, {}
    printer_times: Dict[int, float] = {p.id: 0.0 for p in printers}
    # sort tasks by time descending
    for task in sorted(tasks, key=lambda t: t.time_min, reverse=True):
        compatible = [p for p in printers if is_printer_compatible(p, task)]
        if not compatible:
            unassigned.append(task)
            continue
        best = min(compatible, key=lambda p: printer_times[p.id])
        start = printer_times[best.id]
        duration = task.time_min / best.speed_factor
        end = start + duration
        printer_times[best.id] = end
        assignments.append(AssignmentDTO(best.id, task, start, end))
    makespan = max(printer_times.values()) if printer_times else 0.0
    return assignments, unassigned, makespan, printer_times
