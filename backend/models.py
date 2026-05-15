from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime,
    Text, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
import enum

from database import Base


class ConsentType(str, enum.Enum):
    COLLECTION_USE = "collection_use"   # 수집·이용 동의서
    THIRD_PARTY = "third_party"         # 제3자 제공 동의서


class ConsentStatus(str, enum.Enum):
    DRAFT = "draft"         # 초안
    ACTIVE = "active"       # 시행중
    INACTIVE = "inactive"   # 미사용


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)   # 서비스 코드
    name = Column(String(200), nullable=False)               # 서비스명
    description = Column(Text, nullable=True)                # 설명
    department = Column(String(100), nullable=True)          # 담당 부서
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    consent_forms = relationship("ConsentForm", back_populates="service", cascade="all, delete-orphan")


class ConsentForm(Base):
    """수집이용 및 제3자 제공 동의서 통합 테이블"""
    __tablename__ = "consent_forms"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    consent_type = Column(SAEnum(ConsentType), nullable=False)
    is_required = Column(Boolean, default=True)              # 필수/선택
    status = Column(SAEnum(ConsentStatus), default=ConsentStatus.DRAFT)
    version = Column(String(20), nullable=False, default="1.0")
    effective_date = Column(Date, nullable=True)             # 시행일

    # 공통
    purpose = Column(Text, nullable=False)                   # 수집·이용 목적 / 제공 목적
    items = Column(Text, nullable=False)                     # 수집 항목 / 제공 항목
    retention_period = Column(String(200), nullable=False)   # 보유·이용 기간
    refusal_consequence = Column(Text, nullable=True)        # 거부 시 불이익

    # 제3자 제공 전용
    recipient = Column(String(200), nullable=True)           # 제공받는 자
    recipient_purpose = Column(Text, nullable=True)          # 수신사 이용 목적
    recipient_retention_period = Column(String(200), nullable=True)  # 수신사 보유기간

    memo = Column(Text, nullable=True)                       # 담당자 메모
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    service = relationship("Service", back_populates="consent_forms")
    history = relationship("ConsentFormHistory", back_populates="consent_form", cascade="all, delete-orphan")


class ConsentFormHistory(Base):
    """동의서 개정 이력"""
    __tablename__ = "consent_form_history"

    id = Column(Integer, primary_key=True, index=True)
    consent_form_id = Column(Integer, ForeignKey("consent_forms.id"), nullable=False)
    version = Column(String(20), nullable=False)
    snapshot = Column(Text, nullable=False)    # JSON 직렬화된 이전 버전 내용
    changed_by = Column(String(100), nullable=True)
    change_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    consent_form = relationship("ConsentForm", back_populates="history")
