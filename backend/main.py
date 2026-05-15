import json
import subprocess
import sys
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
import os

from database import Base, engine, get_db
from models import Service, ConsentForm, ConsentFormHistory, ConsentType, ConsentStatus
from schemas import (
    ServiceCreate, ServiceUpdate, ServiceOut,
    ConsentFormCreate, ConsentFormUpdate, ConsentFormOut, ConsentFormHistoryOut,
    DashboardStats,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="개인정보 동의서 관리 시스템", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 대시보드 ──────────────────────────────────────────────────────────────────

@app.get("/api/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    forms = db.query(ConsentForm)
    return DashboardStats(
        total_services=db.query(Service).count(),
        total_consent_forms=forms.count(),
        collection_use_count=forms.filter(ConsentForm.consent_type == ConsentType.COLLECTION_USE).count(),
        third_party_count=forms.filter(ConsentForm.consent_type == ConsentType.THIRD_PARTY).count(),
        active_count=forms.filter(ConsentForm.status == ConsentStatus.ACTIVE).count(),
        draft_count=forms.filter(ConsentForm.status == ConsentStatus.DRAFT).count(),
        inactive_count=forms.filter(ConsentForm.status == ConsentStatus.INACTIVE).count(),
        required_count=forms.filter(ConsentForm.is_required == True).count(),
        optional_count=forms.filter(ConsentForm.is_required == False).count(),
    )


# ── 서비스 관리 ───────────────────────────────────────────────────────────────

@app.get("/api/services", response_model=List[ServiceOut])
def list_services(
    q: Optional[str] = Query(None, description="서비스명/코드 검색"),
    db: Session = Depends(get_db),
):
    query = db.query(Service)
    if q:
        query = query.filter(
            (Service.name.contains(q)) | (Service.code.contains(q))
        )
    return query.order_by(Service.created_at.desc()).all()


@app.post("/api/services", response_model=ServiceOut, status_code=201)
def create_service(body: ServiceCreate, db: Session = Depends(get_db)):
    if db.query(Service).filter(Service.code == body.code).first():
        raise HTTPException(400, "이미 사용 중인 서비스 코드입니다.")
    svc = Service(**body.model_dump())
    db.add(svc)
    db.commit()
    db.refresh(svc)
    return svc


@app.get("/api/services/{service_id}", response_model=ServiceOut)
def get_service(service_id: int, db: Session = Depends(get_db)):
    svc = db.query(Service).filter(Service.id == service_id).first()
    if not svc:
        raise HTTPException(404, "서비스를 찾을 수 없습니다.")
    return svc


@app.put("/api/services/{service_id}", response_model=ServiceOut)
def update_service(service_id: int, body: ServiceUpdate, db: Session = Depends(get_db)):
    svc = db.query(Service).filter(Service.id == service_id).first()
    if not svc:
        raise HTTPException(404, "서비스를 찾을 수 없습니다.")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(svc, k, v)
    svc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(svc)
    return svc


@app.delete("/api/services/{service_id}", status_code=204)
def delete_service(service_id: int, db: Session = Depends(get_db)):
    svc = db.query(Service).filter(Service.id == service_id).first()
    if not svc:
        raise HTTPException(404, "서비스를 찾을 수 없습니다.")
    db.delete(svc)
    db.commit()


# ── 동의서 관리 ───────────────────────────────────────────────────────────────

@app.get("/api/consent-forms", response_model=List[ConsentFormOut])
def list_consent_forms(
    service_id: Optional[int] = None,
    consent_type: Optional[ConsentType] = None,
    status: Optional[ConsentStatus] = None,
    is_required: Optional[bool] = None,
    q: Optional[str] = Query(None, description="목적/항목/수신사 검색"),
    db: Session = Depends(get_db),
):
    query = db.query(ConsentForm)
    if service_id:
        query = query.filter(ConsentForm.service_id == service_id)
    if consent_type:
        query = query.filter(ConsentForm.consent_type == consent_type)
    if status:
        query = query.filter(ConsentForm.status == status)
    if is_required is not None:
        query = query.filter(ConsentForm.is_required == is_required)
    if q:
        query = query.filter(
            ConsentForm.purpose.contains(q)
            | ConsentForm.items.contains(q)
            | ConsentForm.recipient.contains(q)
        )
    return query.order_by(ConsentForm.updated_at.desc()).all()


@app.post("/api/consent-forms", response_model=ConsentFormOut, status_code=201)
def create_consent_form(body: ConsentFormCreate, db: Session = Depends(get_db)):
    if not db.query(Service).filter(Service.id == body.service_id).first():
        raise HTTPException(404, "서비스를 찾을 수 없습니다.")
    form = ConsentForm(**body.model_dump())
    db.add(form)
    db.commit()
    db.refresh(form)
    return form


@app.get("/api/consent-forms/{form_id}", response_model=ConsentFormOut)
def get_consent_form(form_id: int, db: Session = Depends(get_db)):
    form = db.query(ConsentForm).filter(ConsentForm.id == form_id).first()
    if not form:
        raise HTTPException(404, "동의서를 찾을 수 없습니다.")
    return form


@app.put("/api/consent-forms/{form_id}", response_model=ConsentFormOut)
def update_consent_form(form_id: int, body: ConsentFormUpdate, db: Session = Depends(get_db)):
    form = db.query(ConsentForm).filter(ConsentForm.id == form_id).first()
    if not form:
        raise HTTPException(404, "동의서를 찾을 수 없습니다.")

    # 이력 스냅샷 저장
    snapshot = {
        "version": form.version,
        "purpose": form.purpose,
        "items": form.items,
        "retention_period": form.retention_period,
        "refusal_consequence": form.refusal_consequence,
        "recipient": form.recipient,
        "recipient_purpose": form.recipient_purpose,
        "recipient_retention_period": form.recipient_retention_period,
        "status": form.status.value,
        "is_required": form.is_required,
        "effective_date": str(form.effective_date) if form.effective_date else None,
    }
    history = ConsentFormHistory(
        consent_form_id=form.id,
        version=form.version,
        snapshot=json.dumps(snapshot, ensure_ascii=False),
        changed_by=body.changed_by,
        change_note=body.change_note,
    )
    db.add(history)

    update_data = body.model_dump(exclude_none=True, exclude={"change_note", "changed_by"})
    for k, v in update_data.items():
        setattr(form, k, v)
    form.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(form)
    return form


@app.delete("/api/consent-forms/{form_id}", status_code=204)
def delete_consent_form(form_id: int, db: Session = Depends(get_db)):
    form = db.query(ConsentForm).filter(ConsentForm.id == form_id).first()
    if not form:
        raise HTTPException(404, "동의서를 찾을 수 없습니다.")
    db.delete(form)
    db.commit()


# ── 이력 조회 ─────────────────────────────────────────────────────────────────

@app.get("/api/consent-forms/{form_id}/history", response_model=List[ConsentFormHistoryOut])
def get_consent_form_history(form_id: int, db: Session = Depends(get_db)):
    form = db.query(ConsentForm).filter(ConsentForm.id == form_id).first()
    if not form:
        raise HTTPException(404, "동의서를 찾을 수 없습니다.")
    return (
        db.query(ConsentFormHistory)
        .filter(ConsentFormHistory.consent_form_id == form_id)
        .order_by(ConsentFormHistory.created_at.desc())
        .all()
    )


# ── 스크래퍼 현황 / 실행 API ─────────────────────────────────────────────────

from scraper.config import SCRAPE_CONFIGS

class ScrapeStatusItem(BaseModel):
    service_code: str
    service_name: str
    auto_available: bool     # Playwright 자동 수집 가능 여부
    manual: bool             # 수동 입력 필요
    manual_reason: str
    has_consent_forms: bool  # DB에 동의서 등록 여부
    consent_form_count: int


@app.get("/api/scraper/status", response_model=List[ScrapeStatusItem])
def get_scraper_status(db: Session = Depends(get_db)):
    """35개 서비스의 자동/수동 수집 가능 여부 및 등록 현황 반환"""
    result = []
    for cfg in SCRAPE_CONFIGS:
        svc = db.query(Service).filter(Service.code == cfg.service_code).first()
        if not svc:
            continue
        count = db.query(ConsentForm).filter(ConsentForm.service_id == svc.id).count()
        result.append(ScrapeStatusItem(
            service_code=cfg.service_code,
            service_name=svc.name,
            auto_available=not cfg.manual and bool(cfg.entry_url),
            manual=cfg.manual or not bool(cfg.entry_url),
            manual_reason=cfg.manual_reason,
            has_consent_forms=count > 0,
            consent_form_count=count,
        ))
    return result


_scrape_log: list[str] = []
_scrape_running = False


class ScrapeRequest(BaseModel):
    service_code: str = ""   # 비어있으면 전체 자동 가능 서비스
    headless: bool = True


def _run_scraper(service_code: str, headless: bool):
    global _scrape_running, _scrape_log
    _scrape_running = True
    _scrape_log = []
    try:
        cmd = [sys.executable, "-m", "scraper.runner"]
        if service_code:
            cmd += ["--code", service_code]
        if not headless:
            cmd += ["--headful"]
        proc = subprocess.run(
            cmd,
            capture_output=True, text=True,
            cwd=os.path.dirname(__file__),
        )
        _scrape_log = (proc.stdout + proc.stderr).splitlines()
    finally:
        _scrape_running = False


@app.post("/api/scraper/run")
def run_scraper(body: ScrapeRequest, background_tasks: BackgroundTasks):
    """스크래퍼 백그라운드 실행 (결과는 /api/scraper/log 로 조회)"""
    global _scrape_running
    if _scrape_running:
        raise HTTPException(409, "이미 수집 중입니다. 완료 후 다시 시도해주세요.")
    background_tasks.add_task(_run_scraper, body.service_code, body.headless)
    return {"message": "수집 시작됨", "service_code": body.service_code or "전체"}


@app.get("/api/scraper/log")
def get_scraper_log():
    return {"running": _scrape_running, "log": _scrape_log}


# ── 정적 파일 (프론트엔드) ────────────────────────────────────────────────────

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))
