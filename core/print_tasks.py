from dataclasses import dataclass
from typing import List, Tuple, Optional
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
    done_qty: int
    remaining_qty: int
    capacity: float
    remaining_time_h: Optional[float]
    tasks: List[TaskInfo]


def calculate_order_times(order: ProductionOrder) -> Tuple[List[ComponentInfo], float]:
    """Calcula tempos agregados de impressão para uma ordem de produção."""
    stats: List[ComponentInfo] = []
    for bom in order.product.bom_items.select_related("component"):
        comp = bom.component
        required = order.required_for_component(comp)
        t_piece = (comp.print_time_min or 0) / 60.0
        done = order.printed_for_component(comp)
        remaining_qty = max(required - done, 0)
        tasks = list(
            order.print_tasks.filter(component=comp, printer__is_active=True).select_related("printer")
        )
        assigned = sum(t.quantity for t in tasks)
        capacity = sum((t.printer.speed_factor or 1.0) for t in tasks)
        if assigned > required:
            raise ValidationError(
                f"A soma das quantidades das tarefas para o componente {comp.name} ({assigned}) excede a quantidade necessária ({required}). Ajuste as tarefas."
            )
        task_infos: List[TaskInfo] = []
        for t in tasks:
            speed = t.printer.speed_factor or 1.0
            task_time = (t.quantity * t_piece) / speed
            task_infos.append(TaskInfo(t, task_time))
        if remaining_qty > 0 and capacity > 0:
            remaining_time = (remaining_qty * t_piece) / capacity
        elif remaining_qty > 0:
            remaining_time = None
        else:
            remaining_time = 0.0
        stats.append(
            ComponentInfo(
                component=comp,
                t_piece_h=t_piece,
                required_qty=required,
                done_qty=done,
                remaining_qty=remaining_qty,
                capacity=capacity,
                remaining_time_h=remaining_time,
                tasks=task_infos,
            )
        )
    total = max(
        (s.remaining_time_h for s in stats if s.remaining_time_h is not None),
        default=0.0,
    )
    return stats, total
