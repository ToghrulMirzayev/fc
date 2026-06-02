from dataclasses import dataclass
from typing import Optional, List


@dataclass
class KPINotation:
    direction: str
    text: str


@dataclass
class KPICard:
    label: str
    value: str
    unit: Optional[str]
    delta: Optional[KPINotation]
    spark: List[float]


@dataclass
class AttendanceStats:
    current: List[int]
    previous: List[int]
    y_max: int
    x_labels: List[str]


@dataclass
class ExpiringMember:
    id: str
    name: str
    initials: str
    plan: str
    days_left: int
    expires_on: str
    avatar_gradient: str


@dataclass
class DashboardResponse:
    kpis: List[KPICard]
    attendance: AttendanceStats
    expiring: List[ExpiringMember]
