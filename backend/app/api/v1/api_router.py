from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.devices import router as devices_router
from app.api.v1.telemetry import router as telemetry_router
from app.api.v1.events import router as events_router
from app.api.v1.commands import router as commands_router
from app.api.v1.policies import router as policies_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.audit import router as audit_router
from app.api.v1.ws import router as ws_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(devices_router)
api_v1_router.include_router(telemetry_router)
api_v1_router.include_router(events_router)
api_v1_router.include_router(commands_router)
api_v1_router.include_router(policies_router)
api_v1_router.include_router(evidence_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(ws_router)
