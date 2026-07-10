from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class MemberItem:
    id: str
    full_name: str
    phone: str
    initials: str
    status: str
    plan_name: str
    plan_type: str
    expires_on: str
    days_left: int
    visits_remaining: Optional[int]
    visit_limit: Optional[int]


@dataclass
class MembersResponse:
    items: List[MemberItem]
    total: int
    counts_by_status: Dict[str, int]
