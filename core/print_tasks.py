from dataclasses import dataclass
from typing import List, Tuple
from django.core.exceptions import ValidationError
from .models import ProductionOrder, Component, PrintTask


@dataclass
class TaskInfo:
    task: PrintTask
    time_h: float


@dataclass
class ComponentInfo:
    component: Component
    t_piece_h: float
    required_qty: int
    assigned_qty: int
    remaining_qty: int
    capacity: float
    time_h: float
    remaining_time_h: float
    tasks: List[TaskInfo]


def calculate_order_times(order: ProductionOrder) -> Tuple[List[ComponentInfo], float]:
    """Calcula tempos agregados de impressão para uma ordem de produção."""
    stats: List[ComponentInfo] = []
    for bom in order.product.bom_items.select_related("component"):
        comp = bom.component
        required = order.required_for_component(comp)
        t_piece = (comp.print_time_min or 0) / 60.0
        tasks = list(order.print_tasks.filter(component=comp).select_related("printer"))
        assigned = sum(t.quantity for t in tasks)
        capacity = sum((t.printer.speed_factor or 1.0) for t in tasks)
        task_infos: List[TaskInfo] = []
        for t in tasks:
            speed = t.printer.speed_factor or 1.0
            task_time = (t.quantity * t_piece) / speed
            task_infos.append(TaskInfo(t, task_time))
        comp_time = (assigned * t_piece) / capacity if capacity > 0 else 0.0
        remaining_qty = max(required - assigned, 0)
        remaining_time = remaining_qty * t_piece
        if assigned > required:
            raise ValidationError(
                f"A soma das quantidades das tarefas para o componente {comp.name} ({assigned}) excede a quantidade necessária ({required}). Ajuste as tarefas."
            )
        stats.append(
            ComponentInfo(
                component=comp,
                t_piece_h=t_piece,
                required_qty=required,
                assigned_qty=assigned,
                remaining_qty=remaining_qty,
                capacity=capacity,
                time_h=comp_time,
                remaining_time_h=remaining_time,
                tasks=task_infos,
            )
        )
    total = max((s.time_h for s in stats), default=0.0)
    return stats, total
