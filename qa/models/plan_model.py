from dataclasses import dataclass
from typing import Optional


@dataclass
class Plan:
    id: str
    name: str
    type: str
    price: str
    duration_days: int
    visit_limit: Optional[int]
    max_freeze_days: int
    max_freeze_count: int
    is_active: bool
