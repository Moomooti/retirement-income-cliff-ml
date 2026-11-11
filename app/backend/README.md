# 미리사주 백엔드 (FastAPI)

| 경로 | 내용 |
|---|---|
| `POST /predict` | 화면 입력 21개 → 2년 뒤 소득절벽 위험 (서비스 모델 S20/S21, 지금 기준선 아래면 B20). `ENABLE_PREDICT=1`일 때만 켜짐, 아니면 503 |
| `POST /chat` | Claude API 중계 챗봇 (CHAT.md) |
| `GET /health` | `{"status":"ok","predict":true/false}` |

## 구조
| 파일 | 내용 |
|---|---|
| app/main.py | 엔드포인트, 입력 검증, 응답 변환 |
| app/model_core.py | 모델 패키지의 predict.py 그대로 (수정 없음) |
| app/model/ | S20(건강 제외)·S21(건강 포함)·B20(지금 기준선 아래) 모델, constants.json(빈곤선·CPI) |
| app/chat.py | 챗봇 |
| tests/ | 패키지 일치 테스트 + API 일치(300건)·계약·검증·CORS·로그·챗봇 (22개) |
| Dockerfile | Render 배포용 (PORT 환경변수 사용) |

## 실행
```
pip install -r requirements-dev.txt
python -m pytest -q tests
ENABLE_PREDICT=1 ALLOWED_ORIGINS=http://localhost:8765 uvicorn app.main:app --port 8000 --no-access-log
```

## /predict 요청 (모두 필수, health만 선택)
birth_year, female(0/1), married(0/1), edu3(0 고졸 미만·1 고졸·2 대졸 이상), hh_size, hh_size_2y,
pension_recv, retire_pension, private_pension (0/1), income_now, income_1y, income_2y (가구 월 실수령, 만원),
employed, employed_1y, employed_2y (0/1), job_type(regular·temp·self·other·none), owner(0/1),
fin_asset, real_asset(소유한 집·건물·토지 시세 합계, 전세보증금 제외), debt(잔액), health(1~5, 선택)

## 응답
- 대상: `{eligible:true, ratio_now, mode, band(high/mid/low), top_pct, abstain, reasons[{feature,label,effect}], programs:[], model{version,note}}`
  - `mode='above'`: 지금 기준선 위 → 2년 뒤 반복해서 기준선 아래로 내려갈 쪽 순위 (S20/S21)
  - `mode='below'`: 지금 기준선 아래 → 2년 뒤에도 아래에 머물 쪽 순위 (B20, prereg_B 통과: 시험 AUC 0.813 vs 지금 소득만 0.690)
- 대상 아님(50~69세 밖, 지금 소득 0): `{eligible:false, ratio_now, reason, model{note}}`

## 운영 원칙
- 요청 본문 저장·로그 금지(접근 로그 끔, 예외는 종류만), CORS는 ALLOWED_ORIGINS만, 원자료 없음
- 패널 자료로 학습한 모델이라, 공개 서비스로 켜기(ENABLE_PREDICT=1) 전에 각 패널 기관의 이용 조건을 확인한다
