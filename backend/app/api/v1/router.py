"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import auth, dashboard, members, operations, public

router = APIRouter()
router.include_router(public.router)
router.include_router(auth.router)
router.include_router(dashboard.router)
router.include_router(members.router)
router.include_router(operations.plans_router)
router.include_router(operations.payments_router)
router.include_router(operations.checkins_router)
