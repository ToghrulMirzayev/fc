"""Pydantic response schemas for dashboard endpoints.

Shapes are aligned with the frontend's KpiCard, AttendanceChart, and
ExpiringList components. Frontend imports types via OpenAPI codegen
later — for now both sides hand-maintain the contract.
"""

from datetime import date

from pydantic import BaseModel


class Delta(BaseModel):
    direction: str  # "up" | "down"
    text: str


class KpiOut(BaseModel):
    label: str
    value: str
    unit: str | None = None
    delta: Delta | None = None
    spark: list[float]  # normalized 0..1 values


class AttendanceSeriesOut(BaseModel):
    current: list[int]
    previous: list[int]
    y_max: int
    x_labels: list[str]


class ExpiringMemberOut(BaseModel):
    id: str
    name: str
    initials: str
    plan: str
    days_left: int
    expires_on: date
    avatar_gradient: str  # tailwind class hint for now


class DashboardOut(BaseModel):
    """Everything the dashboard page needs in one call.

    Single round-trip is fine for v1.0 — gym dashboards have a fixed
    set of widgets. If we later add user-configurable dashboards, split
    into per-widget endpoints.
    """

    kpis: list[KpiOut]
    attendance: AttendanceSeriesOut
    expiring: list[ExpiringMemberOut]
