"""
현대자동차 운영 서비스 마스터 목록 기준 초기 데이터 등록 스크립트
출처: HMC 서비스 마스터 목록 v2.0 (2026년 5월, 개인정보보호팀)
"""
from database import Base, engine, SessionLocal
from models import Service

Base.metadata.create_all(bind=engine)

SERVICES = [
    # ── 1. 메인 포털 / 차량 구매 ────────────────────────────────────────────
    {
        "code": "HMC_WEB_MAIN",
        "name": "현대닷컴",
        "department": "디지털마케팅팀",
        "description": "현대자동차 공식 웹사이트. 시승신청·구매상담·정비예약·마이페이지 회원가입 시 동의서 노출. 법 제15조·제17조 해당.",
    },
    {
        "code": "HMC_WEB_CASPER",
        "name": "캐스퍼 온라인",
        "department": "디지털마케팅팀",
        "description": "온라인 차량 계약·결제·인수 전 과정. 법 제15조·제17조·제24조(고유식별정보) 해당.",
    },
    {
        "code": "HMC_WEB_CERTIFIED",
        "name": "현대/제네시스 인증중고차",
        "department": "중고차사업팀",
        "description": "회원가입, 내차팔기 신청, 차량번호 조회. 법 제15조·제17조·제24조 해당.",
    },
    {
        "code": "HMC_WEB_MYHYUNDAI_PORTAL",
        "name": "myHyundai 웹포털",
        "department": "디지털플랫폼팀",
        "description": "통합 로그인·마이페이지·차량 등록. 법 제15조·제17조 해당.",
    },
    {
        "code": "HMC_WEB_WORLDWIDE",
        "name": "현대차 글로벌(월드와이드)",
        "department": "글로벌마케팅팀",
        "description": "뉴스레터 구독 시 이메일 수집. 법 제15조 해당.",
    },

    # ── 2. 커머스 / 쇼핑 ────────────────────────────────────────────────────
    {
        "code": "HMC_WEB_SHOP",
        "name": "현대샵(HyundaiShop)",
        "department": "커머스사업팀",
        "description": "회원가입·상품 결제·블루멤버스 포인트 연동. 법 제15조·제17조 해당.",
    },
    {
        "code": "HMC_WEB_COLLECTION",
        "name": "현대 컬렉션 온라인샵",
        "department": "브랜드커머스팀",
        "description": "회원가입·굿즈 구매·결제. INNOCEAN/ROBOT Collection Co. 위탁 운영 — 수탁자 명시 여부 확인 필요(법 제26조). 법 제15조·제17조 해당.",
    },

    # ── 3. 통합 앱 / 커넥티비티 ─────────────────────────────────────────────
    {
        "code": "HMC_APP_MYHYUNDAI",
        "name": "마이현대(myHyundai) ★핵심",
        "department": "커넥티드서비스팀",
        "description": "통합ID 회원가입·차량 등록·블루링크 개통·디지털키 발급·현대페이 등록. 위치·카메라·블루투스·차량정보 등 민감 권한 포함. 법 제15조·제17조 해당.",
    },
    {
        "code": "HMC_APP_BLUELINK_OLD",
        "name": "현대 블루링크(구, 서비스 종료)",
        "department": "커넥티드서비스팀",
        "description": "2025.6.25 마이현대로 통합 종료. 과거 동의서 이력 및 커넥티드카 정보 수집 이력 보존 필요.",
    },
    {
        "code": "HMC_APP_DIGITALKEY",
        "name": "현대 디지털키 1/2",
        "department": "커넥티드서비스팀",
        "description": "마이현대 앱 내 기능. 디지털키 발급·공유 시 추가 동의. NFC·UWB·BLE 활용. 법 제15조 해당.",
    },
    {
        "code": "HMC_APP_CARPAY",
        "name": "인카페이먼트(현대 카페이)",
        "department": "커넥티드서비스팀",
        "description": "마이현대 앱 내 기능. 카드 등록·인카페이먼트 서비스 이용 동의. 결제정보 수집. 법 제15조·제17조(금융사) 해당.",
    },
    {
        "code": "HMC_WEB_BLUELINK_REG",
        "name": "블루링크 가입안내 사이트",
        "department": "커넥티드서비스팀",
        "description": "블루링크 가입 유도 → 마이현대 앱으로 이동. 정보 제공 목적, 동의서 직접 노출 적음.",
    },

    # ── 4. 모빌리티 / 충전 / 구독 ────────────────────────────────────────────
    {
        "code": "HMC_APP_EPIT",
        "name": "E-pit(이피트)",
        "department": "전동화사업팀",
        "description": "충전 회원 가입·차량·결제정보 등록·멤버십 가입. Web+App. 법 제15조·제17조 해당.",
    },
    {
        "code": "HMC_APP_HICHARGER",
        "name": "Hi-Charger(하이차저)",
        "department": "전동화사업팀",
        "description": "충전소 예약·결제. 마이현대 통합 진행 중. 법 제15조 해당.",
    },
    {
        "code": "HMC_APP_SELECTION",
        "name": "현대/제네시스 셀렉션",
        "department": "구독서비스팀",
        "description": "차량 구독 계약·운전면허·결제정보 제공. 법 제15조·제17조·제24조(운전면허번호) 해당.",
    },
    {
        "code": "HMC_APP_SHUCLE",
        "name": "셔클(SHUCLE)",
        "department": "모빌리티팀",
        "description": "회원가입·결제정보·위치정보 수집. 법 제15조·위치정보법 해당.",
    },
    {
        "code": "HMC_APP_TTOKTA",
        "name": "똑타(경기도 DRT)",
        "department": "모빌리티팀",
        "description": "회원가입·대중교통 통합 결제. 법 제15조·위치정보법 해당.",
    },
    {
        "code": "HMC_APP_EUNGPASS",
        "name": "이응패스(세종시)",
        "department": "모빌리티팀",
        "description": "회원가입·통합 교통패스 결제. 법 제15조·위치정보법 해당.",
    },

    # ── 5. 브랜드 체험 / 교육 ────────────────────────────────────────────────
    {
        "code": "HMC_WEB_MOTORSTUDIO",
        "name": "현대 모터스튜디오",
        "department": "브랜드체험팀",
        "description": "시승·프로그램 예약·운전면허 정보 수집. 법 제15조·제24조(운전면허번호) 해당.",
    },
    {
        "code": "HMC_WEB_DRIVING",
        "name": "HMG 드라이빙 익스피리언스",
        "department": "브랜드체험팀",
        "description": "트랙 주행 교육 예약·결제·면허 확인. 법 제15조·제17조·제24조 해당.",
    },
    {
        "code": "HMC_APP_YESDRIVE",
        "name": "운전결심(Yes I Drive)",
        "department": "브랜드체험팀",
        "description": "회원가입·면허·결제정보·연수 매칭. 법 제15조·제17조·제24조 해당. 민감정보(건강) 수집 가능성 — 법 제23조 확인 필요.",
    },
    {
        "code": "HMC_WEB_YOUNG",
        "name": "영현대(Young Hyundai)",
        "department": "브랜드마케팅팀",
        "description": "기자단·이벤트 지원 시 개인정보 수집. 법 제15조 해당.",
    },
    {
        "code": "HMC_APP_N",
        "name": "Hyundai N 앱",
        "department": "N브랜드팀",
        "description": "블루링크 연동·주행 데이터 수집·랩타임 기록. 법 제15조·위치정보법 해당.",
    },
    {
        "code": "HMC_WEB_N_GLOBAL",
        "name": "현대 N 브랜드 글로벌 사이트",
        "department": "N브랜드팀",
        "description": "뉴스레터 구독·이벤트 참여 시 수집. 법 제15조 해당.",
    },

    # ── 6. 채용 ─────────────────────────────────────────────────────────────
    {
        "code": "HMC_WEB_TALENT",
        "name": "현대자동차 인재채용(통합 포털) ★핵심",
        "department": "인재채용팀",
        "description": "회원가입·지원서 작성·제출·전형 조회. 학력·경력·자격증·병역·가족관계 수집. 법 제15조·제23조(민감정보)·제24조(고유식별정보) 해당. 정밀 검토 권고.",
    },
    {
        "code": "HMC_WEB_TALENT_BRAND",
        "name": "직무 안내·채용 브랜딩 사이트",
        "department": "인재채용팀",
        "description": "이벤트 신청(Team Hyundai Talk Live 등) 시 수집. 법 제15조 해당.",
    },
    {
        "code": "HMC_WEB_TALENT_TECH",
        "name": "기술인력 채용 사이트",
        "department": "인재채용팀",
        "description": "생산·기술직 별도 지원서 작성·제출. 학력·자격·병역 수집. 법 제15조·제24조 해당.",
    },

    # ── 7. 기업정보 / 대외 소통 ─────────────────────────────────────────────
    {
        "code": "HMC_WEB_IR",
        "name": "투자자 정보(IR)",
        "department": "IR팀",
        "description": "IR 뉴스레터 구독 시 이메일 수집. 주로 기업 공시용, 동의서 노출 제한적. 법 제15조 해당.",
    },
    {
        "code": "HMC_WEB_NEWSROOM",
        "name": "뉴스룸(Newsroom)",
        "department": "홍보팀",
        "description": "미디어 키트 요청·기자 등록 시 수집. 언론 대상 서비스. 법 제15조 해당.",
    },
    {
        "code": "HMC_WEB_DIVIDEND",
        "name": "배당조회 서비스",
        "department": "주주서비스팀",
        "description": "주주 본인 확인·배당내역 조회. 주주 대상, 고유식별정보 활용 가능. 법 제15조·제24조 해당.",
    },
    {
        "code": "HMC_WEB_AUDIT",
        "name": "사이버 감사실",
        "department": "감사팀",
        "description": "제보자 정보(선택) 수집. 익명 제보 가능. 법 제15조 해당.",
    },
    {
        "code": "HMC_WEB_SUSTAINABILITY",
        "name": "지속가능경영 포털",
        "department": "ESG전략팀",
        "description": "보고서 다운로드·이메일 구독. ESG 정보 공개용. 법 제15조 해당.",
    },
    {
        "code": "HMC_WEB_HRI",
        "name": "현대 경제산업연구원(HRI)",
        "department": "HRI",
        "description": "보고서 구독·세미나 신청. 현대차 부설 연구원, 회원가입 필요. 법 제15조 해당.",
    },

    # ── 8. B2B / 협력사 (참고 — 1차 범위 제외 권고) ─────────────────────────
    {
        "code": "HMC_WEB_WINWIN",
        "name": "동반성장 포털(구)",
        "department": "동반성장팀",
        "description": "1차 협력사 대상 동반성장 프로그램. B2B 서비스 — 대고객 1차 범위 제외 권고.",
    },
    {
        "code": "HMC_WEB_WINWIN23",
        "name": "HMG 상생협력실천센터",
        "department": "동반성장팀",
        "description": "현대·기아 1~2차 협력사 ESG·자금지원. B2B 서비스 — 대고객 1차 범위 제외 권고.",
    },
]


def run():
    db = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        for svc_data in SERVICES:
            exists = db.query(Service).filter(Service.code == svc_data["code"]).first()
            if exists:
                skipped += 1
                continue
            db.add(Service(**svc_data))
            inserted += 1
        db.commit()
        print(f"✅ 완료: {inserted}개 서비스 등록, {skipped}개 이미 존재(스킵)")
    except Exception as e:
        db.rollback()
        print(f"❌ 오류: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
