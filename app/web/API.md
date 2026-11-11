# 미리노후 진단 API 명세 (초안)

프론트(`index.html`)는 `CONFIG.API_BASE`가 비어 있으면 ML 검진을 "모델 서버 연결 준비 중"으로 표시한다.
API가 배포되면 `CONFIG.API_BASE`에 주소만 넣으면 된다. 테스트할 때는 `index.html?api=http://localhost:8000`처럼 붙여도 된다.

> 서비스 모델(사람이 직접 답할 수 있는 질문만 쓰는 모델)은 검증 전이다. 검증 결과에 따라 입력 항목이 바뀔 수 있다.

## POST /predict

### 요청 (JSON, 금액 단위: 만원)

| 필드 | 타입 | 설명 |
|---|---|---|
| `age` | int | 만 나이 (모델 검증 범위 50~69) |
| `female` | 0/1 | 여성 1 |
| `hh_size` | int | 가구원 수 (본인 포함) |
| `income_month` | int | 지금 가구 한 달 실수령(세후) 소득 |
| `income_min4y_month` | int | 최근 4년 중 가장 적었던 해의 한 달 실수령 소득 |
| `employed` | 0/1 | 지금 일하는지 |
| `lost_job_2y` | 0/1 | 최근 2년 사이 일을 그만뒀는지 |
| `hh_change_2y` | 0/1 | 최근 2년 사이 가구원 수 변화 |
| `pension` | 0/1 | 국민·공무원·사학연금 가입(수령) |
| `fin_asset` | int | 금융자산 |
| `real_asset` | int | 부동산(자가 시세·보증금) |
| `debt` | int | 부채 |

### 응답 (JSON)

```json
{
  "band": "high",            // "high" | "mid" | "low"  (위험 구간: 순위 기준)
  "top_pct": 12,             // 같은 연령대 100명 중 위험 순위(상위 %)
  "abstain": false,          // true면 판단 보류(분할 컨포멀, 두 클래스 모두 가능)
  "reasons": [               // 개인별 이유(TreeSHAP), 효과 크기 순 최대 3개
    {"label": "최근 4년 중 가장 낮았던 소득", "effect": 0.81},
    {"label": "최근 2년 내 실직", "effect": 0.47},
    {"label": "연금 가입", "effect": -0.21}
  ],
  "programs": ["중장년 재취업 지원 상담"],
  "model": {"version": "service-v1", "note": "관측 자료로 학습한 예측이며 미래를 보장하지 않습니다."}
}
```

## GET /health

`{"status": "ok", "model": "service-v1"}`

## 운영 원칙

- 요청 본문은 저장하지 않는다. 접근 로그에도 본문을 남기지 않는다.
- CORS는 배포된 프론트 도메인만 허용한다.
- 원자료(패널 마이크로데이터)는 서버에 두지 않는다. 학습된 모델 파일과 집계값만 배포한다.
- 일치 테스트: 봉인 시험셋 표본을 API에 넣은 점수 = 오프라인 모델 점수.
