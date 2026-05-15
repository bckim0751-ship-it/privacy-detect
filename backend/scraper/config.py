"""
서비스별 동의서 수집 플로우 설정
- auth_required=False : 회원가입 진입 시 인증 전 동의서 (자동 수집 가능)
- auth_required=True  : 로그인 후 서비스 신청 시 동의서 (.env 계정 사용)
- manual=True         : 앱 전용 등 자동화 불가 → 수동 입력 필요
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Step:
    """브라우저 조작 단계 1개"""
    action: str          # "click" | "fill" | "wait" | "wait_for_selector" | "select_option"
    selector: str = ""   # CSS 또는 text= 셀렉터
    value: str = ""      # fill/select 시 입력값, wait 시 ms
    optional: bool = False  # True면 실패해도 계속 진행


@dataclass
class ConsentBlock:
    """동의서 블록 1개 (한 페이지에 여러 동의서가 있을 수 있음)"""
    consent_type: str          # "collection_use" | "third_party"
    is_required: bool
    title_selector: str = ""   # 동의서 제목 셀렉터 (없으면 title 파라미터 사용)
    title: str = ""            # 직접 지정할 제목
    content_selector: str = "" # 동의서 본문 셀렉터


@dataclass
class ScrapeConfig:
    service_code: str
    entry_url: str
    steps: list[Step] = field(default_factory=list)
    consent_blocks: list[ConsentBlock] = field(default_factory=list)
    auth_required: bool = False
    env_email_key: str = ""     # .env의 계정 이메일 키
    env_password_key: str = ""  # .env의 계정 패스워드 키
    manual: bool = False        # True면 자동화 불가 — 수동 입력 필요
    manual_reason: str = ""     # 수동 입력이 필요한 이유


# ─────────────────────────────────────────────────────────────────────────────
# 서비스별 수집 설정 목록
# ─────────────────────────────────────────────────────────────────────────────

SCRAPE_CONFIGS: list[ScrapeConfig] = [

    # ── 1. 메인 포털 / 차량 구매 ────────────────────────────────────────────

    ScrapeConfig(
        service_code="HMC_WEB_MAIN",
        entry_url="https://www.hyundai.com/kr/ko/e/member/sign-up",
        steps=[
            Step("wait_for_selector", "input[type='checkbox'], .agree-wrap, .terms-wrap, [class*='consent']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,
                         content_selector="[class*='required'] [class*='content'], [class*='terms-body']:first-of-type"),
            ConsentBlock("collection_use", False,
                         content_selector="[class*='optional'] [class*='content']"),
            ConsentBlock("third_party", False,
                         content_selector="[class*='third'] [class*='content'], [class*='provide'] [class*='content']"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_CASPER",
        entry_url="https://casper.hyundai.com/purchase/order/new",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='consent'], [class*='terms']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='txt'], [class*='required'] p"),
            ConsentBlock("collection_use", False, content_selector="[class*='optional'] [class*='txt']"),
            ConsentBlock("third_party",    False, content_selector="[class*='third'] p, [class*='provide'] p"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_CERTIFIED",
        entry_url="https://certified.hyundai.com/membership/join/agree",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='content']"),
            ConsentBlock("collection_use", False, content_selector="[class*='optional'] [class*='content']"),
            ConsentBlock("third_party",    False, content_selector="[class*='third'] [class*='content']"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_MYHYUNDAI_PORTAL",
        entry_url="https://www.hyundai.com/kr/ko/e/member/sign-up",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='cont']"),
            ConsentBlock("collection_use", False, content_selector="[class*='optional'] [class*='cont']"),
            ConsentBlock("third_party",    False, content_selector="[class*='third'] [class*='cont']"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_WORLDWIDE",
        entry_url="https://www.hyundai.com/worldwide/ko",
        steps=[
            Step("click", "text=뉴스레터, [class*='newsletter'], [class*='subscribe']", optional=True),
            Step("wait_for_selector", "[class*='agree'], [class*='consent'], [class*='privacy']", optional=True),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True, content_selector="[class*='privacy'] p, [class*='agree'] p"),
        ],
    ),

    # ── 2. 커머스 / 쇼핑 ────────────────────────────────────────────────────

    ScrapeConfig(
        service_code="HMC_WEB_SHOP",
        entry_url="https://shop.hyundai.com/member/join/agree",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='content']"),
            ConsentBlock("collection_use", False, content_selector="[class*='option'] [class*='content']"),
            ConsentBlock("third_party",    False, content_selector="[class*='third'] [class*='content']"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_COLLECTION",
        entry_url="https://collection.hyundai.com/member/join",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='cont']"),
            ConsentBlock("third_party",    False, content_selector="[class*='third'] [class*='cont']"),
        ],
    ),

    # ── 3. 통합 앱 / 커넥티비티 ─────────────────────────────────────────────

    ScrapeConfig(
        service_code="HMC_APP_MYHYUNDAI",
        entry_url="https://www.hyundai.com/kr/ko/e/member/sign-up",
        auth_required=True,
        env_email_key="HMC_MAIN_EMAIL",
        env_password_key="HMC_MAIN_PASSWORD",
        steps=[
            Step("wait_for_selector", "input[name='email'], input[type='email']"),
            Step("fill", "input[name='email'], input[type='email']", "{email}"),
            Step("fill", "input[name='password'], input[type='password']", "{password}"),
            Step("click", "button[type='submit'], .btn-login"),
            Step("wait", "", "2000"),
            Step("click", "text=블루링크, [href*='bluelink'], [class*='bluelink']", optional=True),
            Step("wait_for_selector", "[class*='agree'], [class*='consent']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='content']"),
            ConsentBlock("collection_use", False, content_selector="[class*='option'] [class*='content']"),
            ConsentBlock("third_party",    False, content_selector="[class*='third'] [class*='content']"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_APP_BLUELINK_OLD",
        entry_url="",
        manual=True,
        manual_reason="2025.6.25 서비스 종료. 과거 동의서 원문은 내부 IT팀 또는 아카이브에서 수집 필요.",
    ),

    ScrapeConfig(
        service_code="HMC_APP_DIGITALKEY",
        entry_url="",
        manual=True,
        manual_reason="마이현대 앱 내 기능 — 앱 환경에서만 노출. IT팀 원문 제공 요청 필요.",
    ),

    ScrapeConfig(
        service_code="HMC_APP_CARPAY",
        entry_url="",
        manual=True,
        manual_reason="마이현대 앱 내 인카페이먼트 기능 — 앱 환경에서만 노출. IT팀 원문 제공 요청 필요.",
    ),

    ScrapeConfig(
        service_code="HMC_WEB_BLUELINK_REG",
        entry_url="https://bluelink-reg.hyundai.com",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='privacy']", optional=True),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True, content_selector="[class*='privacy'] p"),
        ],
    ),

    # ── 4. 모빌리티 / 충전 / 구독 ─────────────────────────────────────────

    ScrapeConfig(
        service_code="HMC_APP_EPIT",
        entry_url="https://www.e-pit.co.kr/member/join/agree",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='content']"),
            ConsentBlock("collection_use", False, content_selector="[class*='option'] [class*='content']"),
            ConsentBlock("third_party",    False, content_selector="[class*='third'] [class*='content']"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_APP_HICHARGER",
        entry_url="",
        manual=True,
        manual_reason="앱 전용 서비스. 마이현대 통합 진행 중 — 통합 후 마이현대 동의서와 동일할 가능성 있음.",
    ),

    ScrapeConfig(
        service_code="HMC_APP_SELECTION",
        entry_url="https://selection.hyundai.com/membership/join/agree",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='cont']"),
            ConsentBlock("collection_use", False, content_selector="[class*='option'] [class*='cont']"),
            ConsentBlock("third_party",    False, content_selector="[class*='third'] [class*='cont']"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_APP_SHUCLE",
        entry_url="",
        manual=True,
        manual_reason="앱 전용 서비스. 앱스토어 설치 후 회원가입 플로우에서 수동 확인 필요.",
    ),

    ScrapeConfig(
        service_code="HMC_APP_TTOKTA",
        entry_url="",
        manual=True,
        manual_reason="앱 전용 서비스. 앱스토어 설치 후 회원가입 플로우에서 수동 확인 필요.",
    ),

    ScrapeConfig(
        service_code="HMC_APP_EUNGPASS",
        entry_url="",
        manual=True,
        manual_reason="앱 전용 서비스. 앱스토어 설치 후 회원가입 플로우에서 수동 확인 필요.",
    ),

    # ── 5. 브랜드 체험 / 교육 ────────────────────────────────────────────────

    ScrapeConfig(
        service_code="HMC_WEB_MOTORSTUDIO",
        entry_url="https://motorstudio.hyundai.com/kr/ko/reservation",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms'], [class*='privacy']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='content']"),
            ConsentBlock("collection_use", False, content_selector="[class*='option'] [class*='content']"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_DRIVING",
        entry_url="https://drivingexperience.hyundai.co.kr/reservation",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='cont']"),
            ConsentBlock("collection_use", False, content_selector="[class*='option'] [class*='cont']"),
            ConsentBlock("third_party",    False, content_selector="[class*='third'] [class*='cont']"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_APP_YESDRIVE",
        entry_url="https://yesidrive.hyundai.com/member/join/agree",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='content']"),
            ConsentBlock("collection_use", False, content_selector="[class*='option'] [class*='content']"),
            ConsentBlock("third_party",    False, content_selector="[class*='third'] [class*='content']"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_YOUNG",
        entry_url="https://young.hyundai.com/member/join/agree",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='content']"),
            ConsentBlock("collection_use", False, content_selector="[class*='option'] [class*='content']"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_APP_N",
        entry_url="",
        manual=True,
        manual_reason="앱 전용 서비스 (Hyundai N 앱). 앱스토어 설치 후 블루링크 연동 플로우에서 수동 확인 필요.",
    ),

    ScrapeConfig(
        service_code="HMC_WEB_N_GLOBAL",
        entry_url="https://www.hyundai-n.com",
        steps=[
            Step("click", "text=뉴스레터, [class*='newsletter'], [class*='subscribe']", optional=True),
            Step("wait_for_selector", "[class*='agree'], [class*='privacy']", optional=True),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True, content_selector="[class*='privacy'] p, [class*='consent'] p"),
        ],
    ),

    # ── 6. 채용 ─────────────────────────────────────────────────────────────

    ScrapeConfig(
        service_code="HMC_WEB_TALENT",
        entry_url="https://talent.hyundai.com/member/join/agree",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='content']"),
            ConsentBlock("collection_use", False, content_selector="[class*='option'] [class*='content']"),
            ConsentBlock("third_party",    False, content_selector="[class*='third'] [class*='content']"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_TALENT_BRAND",
        entry_url="https://talent-hyundai-now.com",
        steps=[
            Step("click", "text=이벤트, text=신청, [class*='apply']", optional=True),
            Step("wait_for_selector", "[class*='agree'], [class*='privacy']", optional=True),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True, content_selector="[class*='privacy'] p, [class*='agree'] p"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_TALENT_TECH",
        entry_url="https://technician-talent-hyundai-now.com",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms']", optional=True),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='cont']"),
            ConsentBlock("collection_use", False, content_selector="[class*='option'] [class*='cont']"),
        ],
    ),

    # ── 7. 기업정보 / 대외 소통 ─────────────────────────────────────────────

    ScrapeConfig(
        service_code="HMC_WEB_IR",
        entry_url="https://ir.hyundai.com",
        steps=[
            Step("click", "text=뉴스레터, [class*='newsletter']", optional=True),
            Step("wait_for_selector", "[class*='agree'], [class*='privacy']", optional=True),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True, content_selector="[class*='privacy'] p"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_NEWSROOM",
        entry_url="https://news.hyundai.com",
        steps=[
            Step("click", "text=미디어 등록, text=기자 등록, [class*='media-kit']", optional=True),
            Step("wait_for_selector", "[class*='agree'], [class*='privacy']", optional=True),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True, content_selector="[class*='privacy'] p"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_DIVIDEND",
        entry_url="https://dividend.hyundai.com",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='auth'], [class*='verify']", optional=True),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True, content_selector="[class*='agree'] p, [class*='privacy'] p"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_AUDIT",
        entry_url="https://audit.hyundai.com",
        steps=[
            Step("click", "text=제보하기, [class*='report']", optional=True),
            Step("wait_for_selector", "[class*='agree'], [class*='privacy']", optional=True),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", False, content_selector="[class*='privacy'] p, [class*='agree'] p"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_SUSTAINABILITY",
        entry_url="https://sustainability.hyundai.com",
        steps=[
            Step("click", "text=구독, text=뉴스레터, [class*='subscribe']", optional=True),
            Step("wait_for_selector", "[class*='agree'], [class*='privacy']", optional=True),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True, content_selector="[class*='privacy'] p"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_HRI",
        entry_url="https://hri.co.kr/member/join/agree",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms']"),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True,  content_selector="[class*='required'] [class*='content']"),
            ConsentBlock("collection_use", False, content_selector="[class*='option'] [class*='content']"),
        ],
    ),

    # ── 8. B2B / 협력사 ─────────────────────────────────────────────────────

    ScrapeConfig(
        service_code="HMC_WEB_WINWIN",
        entry_url="http://winwin.hyundai.com",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms']", optional=True),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True, content_selector="[class*='agree'] p"),
        ],
    ),

    ScrapeConfig(
        service_code="HMC_WEB_WINWIN23",
        entry_url="https://winwin23.hyundai.com",
        steps=[
            Step("wait_for_selector", "[class*='agree'], [class*='terms']", optional=True),
        ],
        consent_blocks=[
            ConsentBlock("collection_use", True, content_selector="[class*='agree'] p"),
        ],
    ),
]

# 코드로 빠르게 접근하기 위한 딕셔너리
CONFIGS_BY_CODE: dict[str, ScrapeConfig] = {c.service_code: c for c in SCRAPE_CONFIGS}
