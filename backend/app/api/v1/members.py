"""Members endpoints — the heart of the admin API."""

from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.tenant import require_current_tenant
from app.db.session import get_session
from app.models.member import Member
from app.models.membership import Membership, MembershipStatus
from app.models.plan import MembershipPlan
from app.models.user import User
from app.schemas.member import (
    AssignPlanIn,
    FreezeIn,
    LinkingCodeOut,
    MemberCreate,
    MemberListOut,
    MemberOut,
    MemberUpdate,
)
from app.services.freeze import FreezeError, freeze_membership, resume_membership
from app.services.linking import create_linking_code
from app.services.member import (
    assign_plan,
    compute_member_status,
    create_member,
    get_active_membership,
    initials_of,
    list_members,
    membership_to_brief,
    update_member,
)

router = APIRouter(prefix="/members", tags=["members"])


@router.get("/lookup")
async def lookup_endpoint(
    q: str,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """Find a single member by ID (UUID or MBR_XXX prefix), phone, or email.

    Used by the payments page where staff types whatever identifier they
    have on the member's profile. Returns the first match scoped to the
    current tenant.
    """
    tenant_id = require_current_tenant()
    q_clean = q.strip()
    if not q_clean:
        raise HTTPException(status_code=400, detail="Empty query")

    # Strip MBR_ prefix if present and lowercase for UUID prefix match.
    uuid_hint = q_clean.upper().removeprefix("MBR_").lower()

    # Try exact UUID
    from sqlalchemy import or_, cast, String as SAString
    candidates = await db.execute(
        select(Member).where(
            Member.tenant_id == tenant_id,
            or_(
                cast(Member.id, SAString).ilike(f"{uuid_hint}%"),
                Member.phone.ilike(f"%{q_clean}%"),
                Member.email.ilike(f"%{q_clean}%"),
                Member.full_name.ilike(f"%{q_clean}%"),
            ),
        ).limit(5)
    )
    members = candidates.scalars().all()
    if not members:
        raise HTTPException(status_code=404, detail="Member not found")

    # If single match, return full profile. If multiple, return short list.
    if len(members) == 1:
        member = members[0]
        active = await get_active_membership(db, member.id)
        return {
            "single_match": True,
            "member": {
                "id": str(member.id),
                "full_name": member.full_name,
                "phone": member.phone,
                "email": member.email,
                "initials": initials_of(member.full_name),
                "status": member.status.value,
                "active_membership": (
                    {
                        "id": str(active.id),
                        "plan_name": active.plan_name,
                        "price": str(active.price),
                        "is_paid": active.is_paid,
                    }
                    if active
                    else None
                ),
            },
        }
    return {
        "single_match": False,
        "candidates": [
            {
                "id": str(m.id),
                "full_name": m.full_name,
                "phone": m.phone,
                "initials": initials_of(m.full_name),
            }
            for m in members
        ],
    }


async def _load_member(db: AsyncSession, member_id: UUID) -> Member:
    """Load a member, asserting it belongs to the current tenant."""
    tenant_id = require_current_tenant()
    member = await db.get(Member, member_id)
    if member is None or member.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.get("", response_model=MemberListOut)
async def list_endpoint(
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> MemberListOut:
    items, total, counts = await list_members(
        db,
        status_filter=status_filter,
        search=search,
        limit=limit,
        offset=offset,
    )
    return MemberListOut(items=items, total=total, counts_by_status=counts)


@router.post("", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
async def create_endpoint(
    payload: MemberCreate,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> MemberOut:
    try:
        member = await create_member(db, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MemberOut(
        id=member.id,
        full_name=member.full_name,
        phone=member.phone,
        email=member.email,
        telegram_user_id=member.telegram_user_id,
        locale=member.locale,
        status=member.status.value,
        notes=member.notes,
        initials=initials_of(member.full_name),
        active_membership=None,
    )


@router.get("/{member_id}", response_model=MemberOut)
async def get_endpoint(
    member_id: UUID,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> MemberOut:
    member = await _load_member(db, member_id)
    active = await get_active_membership(db, member.id)
    return MemberOut(
        id=member.id,
        full_name=member.full_name,
        phone=member.phone,
        email=member.email,
        telegram_user_id=member.telegram_user_id,
        locale=member.locale,
        status=member.status.value,
        notes=member.notes,
        initials=initials_of(member.full_name),
        active_membership=(await membership_to_brief(active)) if active else None,
    )


@router.patch("/{member_id}", response_model=MemberOut)
async def update_endpoint(
    member_id: UUID,
    payload: MemberUpdate,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> MemberOut:
    member = await _load_member(db, member_id)
    await update_member(db, member, payload)
    active = await get_active_membership(db, member.id)
    return MemberOut(
        id=member.id,
        full_name=member.full_name,
        phone=member.phone,
        email=member.email,
        telegram_user_id=member.telegram_user_id,
        locale=member.locale,
        status=member.status.value,
        notes=member.notes,
        initials=initials_of(member.full_name),
        active_membership=(await membership_to_brief(active)) if active else None,
    )


@router.post("/{member_id}/linking-code", response_model=LinkingCodeOut)
async def linking_code_endpoint(
    member_id: UUID,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> LinkingCodeOut:
    member = await _load_member(db, member_id)
    code = await create_linking_code(member.id, member.tenant_id)
    return LinkingCodeOut(
        code=code,
        expires_at=date.today() + timedelta(days=1),  # display-only
        member_id=member.id,
    )


@router.post("/{member_id}/assign-plan", status_code=status.HTTP_201_CREATED)
async def assign_plan_endpoint(
    member_id: UUID,
    payload: AssignPlanIn,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    member = await _load_member(db, member_id)
    plan = await db.get(MembershipPlan, payload.plan_id)
    if plan is None or plan.tenant_id != member.tenant_id:
        raise HTTPException(status_code=404, detail="Plan not found")
    try:
        membership = await assign_plan(db, member, plan, payload.starts_on)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"membership_id": str(membership.id)}


@router.post("/{member_id}/freeze")
async def freeze_endpoint(
    member_id: UUID,
    payload: FreezeIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    member = await _load_member(db, member_id)
    membership = await get_active_membership(db, member.id)
    if membership is None:
        raise HTTPException(status_code=400, detail="No active membership")
    try:
        period = await freeze_membership(
            db, membership, payload.ends_on, user.id, payload.reason
        )
    except FreezeError as e:
        raise HTTPException(status_code=400, detail=e.code)
    # Keep the denormalized member.status in sync so the UI updates
    # immediately instead of waiting for the daily recompute task.
    member.status = compute_member_status(membership)
    return {"freeze_period_id": str(period.id)}


@router.post("/{member_id}/resume")
async def resume_endpoint(
    member_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    member = await _load_member(db, member_id)
    membership = await get_active_membership(db, member.id)
    if membership is None or membership.status != MembershipStatus.FROZEN:
        raise HTTPException(status_code=400, detail="Membership not frozen")
    try:
        await resume_membership(db, membership, user.id)
    except FreezeError as e:
        raise HTTPException(status_code=400, detail=e.code)
    member.status = compute_member_status(membership)
    return {"ok": True}


@router.get("/{member_id}/visits")
async def visits_endpoint(
    member_id: UUID,
    limit: int = 50,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    member = await _load_member(db, member_id)
    from app.models.visit import Visit
    result = await db.execute(
        select(Visit)
        .where(Visit.member_id == member.id)
        .order_by(Visit.checked_in_at.desc())
        .limit(limit)
    )
    visits = result.scalars().all()
    return {
        "items": [
            {
                "id": str(v.id),
                "method": v.method.value,
                "checked_in_at": v.checked_in_at.isoformat(),
            }
            for v in visits
        ]
    }
