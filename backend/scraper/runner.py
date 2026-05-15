"""
Playwright 기반 동의서 자동 수집 러너

사용법:
  python -m scraper.runner                     # 전체 자동 수집 가능 서비스
  python -m scraper.runner --code HMC_WEB_MAIN # 특정 서비스만
  python -m scraper.runner --all               # 수동 대상 목록 포함 출력
  python -m scraper.runner --headful           # 브라우저 화면 보면서 디버깅
"""
import argparse
import json
import os
import sys
import re
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트의 .env 로드
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from scraper.config import CONFIGS_BY_CODE, SCRAPE_CONFIGS, ScrapeConfig, ConsentBlock

# DB 접근은 backend 디렉토리 기준
sys.path.insert(0, str(Path(__file__).parent.parent))
from database import SessionLocal
from models import Service, ConsentForm, ConsentType, ConsentStatus


# ── 결과 타입 ─────────────────────────────────────────────────────────────────

class ScrapeResult:
    def __init__(self, service_code: str):
        self.service_code = service_code
        self.success = False
        self.skipped = False   # manual=True인 서비스
        self.error: str = ""
        self.consent_blocks: list[dict] = []

    def __repr__(self):
        status = "✅" if self.success else ("⚠️" if self.skipped else "❌")
        return f"{status} [{self.service_code}] blocks={len(self.consent_blocks)} err={self.error}"


# ── 핵심 수집 엔진 ────────────────────────────────────────────────────────────

def scrape_service(config: ScrapeConfig, headless: bool = True) -> ScrapeResult:
    result = ScrapeResult(config.service_code)

    if config.manual:
        result.skipped = True
        result.error = config.manual_reason
        return result

    if not config.entry_url:
        result.skipped = True
        result.error = "entry_url 미설정 — 수동 입력 필요"
        return result

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        result.error = "playwright 미설치 — pip install playwright && playwright install chromium"
        return result

    timeout = int(os.getenv("SCRAPE_TIMEOUT", "30000"))

    # 계정 정보 로드
    credentials = {}
    if config.auth_required:
        email = os.getenv(config.env_email_key, "")
        password = os.getenv(config.env_password_key, "")
        if not email or not password:
            result.error = f"계정 정보 없음 — .env에 {config.env_email_key}, {config.env_password_key} 설정 필요"
            return result
        credentials = {"email": email, "password": password}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            locale="ko-KR",
        )
        page = context.new_page()
        page.set_default_timeout(timeout)

        try:
            print(f"  → 접속: {config.entry_url}")
            page.goto(config.entry_url, wait_until="networkidle", timeout=timeout)

            # 단계별 실행
            for step in config.steps:
                selector = step.selector
                # {email}/{password} 자리표시자 치환
                value = step.value.format(**credentials) if credentials else step.value

                try:
                    if step.action == "click":
                        # 여러 후보 셀렉터 중 첫 번째 매칭 클릭
                        for sel in selector.split(","):
                            sel = sel.strip()
                            el = page.query_selector(sel)
                            if el:
                                el.click()
                                break

                    elif step.action == "fill":
                        for sel in selector.split(","):
                            sel = sel.strip()
                            el = page.query_selector(sel)
                            if el:
                                el.fill(value)
                                break

                    elif step.action == "wait":
                        page.wait_for_timeout(int(value) if value else 1000)

                    elif step.action == "wait_for_selector":
                        # 여러 후보 중 하나라도 나타나면 진행
                        found = False
                        for sel in selector.split(","):
                            sel = sel.strip()
                            try:
                                page.wait_for_selector(sel, timeout=5000)
                                found = True
                                break
                            except PWTimeout:
                                continue
                        if not found and not step.optional:
                            raise PWTimeout(f"셀렉터 대기 실패: {selector}")

                    elif step.action == "select_option":
                        page.select_option(selector, value)

                except PWTimeout:
                    if not step.optional:
                        raise
                    print(f"    (optional step 타임아웃, 계속 진행): {step.action} {selector[:50]}")

            # 동의서 텍스트 추출
            for block in config.consent_blocks:
                text = ""
                for sel in block.content_selector.split(","):
                    sel = sel.strip()
                    elements = page.query_selector_all(sel)
                    if elements:
                        text = "\n".join(el.inner_text() for el in elements).strip()
                        if text:
                            break

                if text:
                    result.consent_blocks.append({
                        "consent_type": block.consent_type,
                        "is_required": block.is_required,
                        "title": block.title or (
                            "개인정보 수집·이용 동의" if block.consent_type == "collection_use"
                            else "개인정보 제3자 제공 동의"
                        ),
                        "content": text,
                    })
                else:
                    print(f"    ⚠ 블록 텍스트 미추출: {block.consent_type} required={block.is_required}")

            result.success = True

        except Exception as e:
            result.error = str(e)[:200]
        finally:
            browser.close()

    return result


# ── DB 저장 ──────────────────────────────────────────────────────────────────

def save_to_db(result: ScrapeResult) -> int:
    """수집 결과를 DB에 저장. 저장된 동의서 수 반환."""
    if not result.success or not result.consent_blocks:
        return 0

    db = SessionLocal()
    saved = 0
    try:
        svc = db.query(Service).filter(Service.code == result.service_code).first()
        if not svc:
            print(f"  서비스 코드 없음 (DB): {result.service_code}")
            return 0

        for block in result.consent_blocks:
            content = block["content"]

            # 목적, 항목, 보유기간을 본문에서 간단히 파싱 (정규식)
            purpose = _extract(content, r"(수집[·\s]*이용\s*목적|제공\s*목적)[^\n]*\n(.+?)(?:\n|$)")
            items = _extract(content, r"(수집\s*항목|제공\s*항목)[^\n]*\n(.+?)(?:\n|$)")
            retention = _extract(content, r"(보유[·\s]*이용\s*기간|보유\s*기간)[^\n]*\n(.+?)(?:\n|$)")

            form = ConsentForm(
                service_id=svc.id,
                consent_type=ConsentType(block["consent_type"]),
                is_required=block["is_required"],
                status=ConsentStatus.DRAFT,
                version="1.0",
                effective_date=date.today(),
                purpose=purpose or content[:200],
                items=items or "(본문 참조)",
                retention_period=retention or "(본문 참조)",
                refusal_consequence=None,
                memo=f"[자동 수집 {datetime.now().strftime('%Y-%m-%d %H:%M')}]\n\n{content[:2000]}",
            )
            db.add(form)
            saved += 1

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"  DB 저장 오류: {e}")
    finally:
        db.close()

    return saved


def _extract(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.DOTALL)
    if m:
        return m.group(2).strip()[:300]
    return ""


# ── 수동 입력 필요 서비스 보고서 ──────────────────────────────────────────────

def print_manual_report():
    manual = [c for c in SCRAPE_CONFIGS if c.manual or not c.entry_url]
    print(f"\n{'='*60}")
    print(f"수동 입력 필요 서비스 ({len(manual)}개)")
    print(f"{'='*60}")
    for c in manual:
        reason = c.manual_reason or "entry_url 미설정"
        print(f"  [{c.service_code}]")
        print(f"    사유: {reason}\n")


# ── CLI 진입점 ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="HMC 동의서 자동 수집기")
    parser.add_argument("--code", help="특정 서비스 코드만 수집 (예: HMC_WEB_MAIN)")
    parser.add_argument("--all", action="store_true", help="수동 대상 목록까지 출력")
    parser.add_argument("--headful", action="store_true", help="브라우저 화면 표시 (디버깅용)")
    parser.add_argument("--dry-run", action="store_true", help="DB 저장 없이 텍스트만 출력")
    args = parser.parse_args()

    headless = not args.headful

    if args.code:
        targets = [CONFIGS_BY_CODE[args.code]] if args.code in CONFIGS_BY_CODE else []
        if not targets:
            print(f"알 수 없는 서비스 코드: {args.code}")
            sys.exit(1)
    else:
        targets = [c for c in SCRAPE_CONFIGS if not c.manual and c.entry_url]

    print(f"\n▶ 수집 대상: {len(targets)}개 서비스")
    print(f"  headless={headless} | dry-run={args.dry_run}\n")

    results = []
    for config in targets:
        print(f"[{config.service_code}] 수집 시작...")
        result = scrape_service(config, headless=headless)

        if args.dry_run and result.success:
            for b in result.consent_blocks:
                print(f"  [{b['consent_type']} required={b['is_required']}]")
                print(f"  {b['content'][:300]}\n")
        elif not args.dry_run and result.success:
            n = save_to_db(result)
            print(f"  → DB 저장: {n}건")

        results.append(result)
        print(f"  {result}\n")

    # 요약
    ok = sum(1 for r in results if r.success)
    skip = sum(1 for r in results if r.skipped)
    fail = sum(1 for r in results if not r.success and not r.skipped)
    print(f"\n{'='*50}")
    print(f"결과 요약: ✅ 성공 {ok}  ⚠️ 스킵 {skip}  ❌ 실패 {fail}")

    if args.all:
        print_manual_report()


if __name__ == "__main__":
    main()
