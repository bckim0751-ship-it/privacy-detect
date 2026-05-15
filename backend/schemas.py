from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel
from models import ConsentType, ConsentStatus


# ── Service ──────────────────────────────────────────────────────────────────

class ServiceCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    department: Optional[str] = None


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None


class ServiceOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    department: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── ConsentForm ───────────────────────────────────────────────────────────────

class ConsentFormCreate(BaseModel):
    service_id: int
    consent_type: ConsentType
    is_required: bool = True
    status: ConsentStatus = ConsentStatus.DRAFT
    version: str = "1.0"
    effective_date: Optional[date] = None
    purpose: str
    items: str
    retention_period: str
    refusal_consequence: Optional[str] = None
    # 제3자 제공 전용
    recipient: Optional[str] = None
    recipient_purpose: Optional[str] = None
    recipient_retention_period: Optional[str] = None
    memo: Optional[str] = None


class ConsentFormUpdate(BaseModel):
    is_required: Optional[bool] = None
    status: Optional[ConsentStatus] = None
    version: Optional[str] = None
    effective_date: Optional[date] = None
    purpose: Optional[str] = None
    items: Optional[str] = None
    retention_period: Optional[str] = None
    refusal_consequence: Optional[str] = None
    recipient: Optional[str] = None
    recipient_purpose: Optional[str] = None
    recipient_retention_period: Optional[str] = None
    memo: Optional[str] = None
    change_note: Optional[str] = None
    changed_by: Optional[str] = None


class ConsentFormOut(BaseModel):
    id: int
    service_id: int
    consent_type: ConsentType
    is_required: bool
    status: ConsentStatus
    version: str
    effective_date: Optional[date]
    purpose: str
    items: str
    retention_period: str
    refusal_consequence: Optional[str]
    recipient: Optional[str]
    recipient_purpose: Optional[str]
    recipient_retention_period: Optional[str]
    memo: Optional[str]
    created_at: datetime
    updated_at: datetime
    service: ServiceOut

    model_config = {"from_attributes": True}


class ConsentFormHistoryOut(BaseModel):
    id: int
    consent_form_id: int
    version: str
    snapshot: str
    changed_by: Optional[str]
    change_note: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_services: int
    total_consent_forms: int
    collection_use_count: int
    third_party_count: int
    active_count: int
    draft_count: int
    inactive_count: int
    required_count: int
    optional_count: int
