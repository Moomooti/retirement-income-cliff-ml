"""미리사주 진단 API.

진단: 화면 입력 21개를 그대로 받아 model_core.Model.predict 에 넘긴다 (서비스 모델 S20/S21, 사전 등록 기준 통과).
      지금 소득이 기준선 아래면 B20 모델(2년 뒤에도 아래에 머물까, prereg_B 통과) 결과를 mode='below'로 돌려준다.
챗봇: chat.py

운영 원칙
- 요청 본문은 저장하지 않고, 어떤 로그에도 남기지 않는다. (접근 로그는 끄고, 예외도 본문 없이 처리)
- CORS는 ALLOWED_ORIGINS 환경변수의 주소만 허용한다.
- 원자료는 서버에 없다. model/ 폴더의 학습된 모델 파일과 집계 상수만 쓴다.

환경변수
- ALLOWED_ORIGINS : 쉼표로 구분. 기본 https://mirinohulab.github.io
- ENABLE_PREDICT=1 : 진단을 켠다. 기본은 꺼짐(/predict는 503).
  패널 자료로 학습한 모델이라, 공개 서비스로 켜기 전에 각 패널 기관의 이용 조건을 확인한다.
- ANTHROPIC_API_KEY 등 챗봇 설정은 chat.py 참고
"""
import logging
import os
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .chat import router as chat_router

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'model')
NOTE = ('관측 자료로 학습한 예측이며 미래를 보장하지 않습니다. 위험 구간에도 실제로는 괜찮은 사람이 섞여 있어요. '
        '금융·법률 상담을 대신하지 않습니다.')

logging.getLogger('uvicorn.access').disabled = True   # 접근 로그 끔

PREDICT_ON = os.environ.get('ENABLE_PREDICT') == '1'
if PREDICT_ON:
    from .model_core import Model
    model = Model(MODEL_DIR)
else:
    model = None

app = FastAPI(title='미리사주 진단 API', docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(chat_router)
origins = [o.strip() for o in os.environ.get('ALLOWED_ORIGINS', 'https://mirinohulab.github.io').split(',') if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

Bit = Literal[0, 1]


class PredictIn(BaseModel):
    """미리사주 화면 입력. 금액은 만원, 소득은 가구 한 달 실수령(세후)."""
    model_config = ConfigDict(extra='forbid')
    birth_year: int = Field(ge=1930, le=2010)
    female: Bit
    married: Bit
    edu3: Literal[0, 1, 2]                          # 0 고졸 미만, 1 고졸, 2 대졸 이상
    hh_size: int = Field(ge=1, le=20)
    hh_size_2y: int = Field(ge=1, le=20)
    pension_recv: Bit
    retire_pension: Bit
    private_pension: Bit
    income_now: float = Field(ge=0, le=100_000)
    income_1y: float = Field(ge=0, le=100_000)
    income_2y: float = Field(ge=0, le=100_000)
    employed: Bit
    employed_1y: Bit
    employed_2y: Bit
    job_type: Literal['regular', 'temp', 'self', 'other', 'none']
    owner: Bit
    fin_asset: float = Field(ge=0, le=10_000_000)   # 예금·적금·주식·채권·계 등
    real_asset: float = Field(ge=0, le=10_000_000)  # 소유한 집·건물·토지 시세 합계 (전세보증금 제외)
    debt: float = Field(ge=0, le=10_000_000)        # 남은 빚 잔액 (월 상환액 아님)
    health: Optional[Literal[1, 2, 3, 4, 5]] = None  # 1 매우 건강 ~ 5 매우 나쁨, 없으면 건강 제외 모델


def _num(v):
    return None if v is None or v != v else round(float(v), 3)


def to_response(r: dict) -> dict:
    """모델 결과 → API 응답. 점수 원값(lgb, lr)은 내보내지 않는다."""
    base = {'eligible': bool(r['eligible']), 'ratio_now': _num(r.get('ratio_now'))}
    if not r['eligible']:
        return {**base, 'reason': r['reason'], 'model': {'note': NOTE}}
    return {
        **base,
        'mode': r.get('mode', 'above'),              # 'above' 지금 기준선 위 / 'below' 지금 기준선 아래(B20)
        'band': r['band'],
        'top_pct': round(r['top_pct'], 1),
        'abstain': bool(r['abstain']),
        'reasons': [{'feature': x['feature'], 'label': x['label'], 'effect': round(x['effect'], 3)} for x in r['reasons']],   # feature: 화면이 내 값으로 문장을 만드는 데 씀
        'programs': [],                              # 권장 제도 규칙은 아직 정하지 않음 (프론트는 빈 목록이면 숨김)
        'model': {'version': r.get('model'), 'note': NOTE},
    }


@app.exception_handler(Exception)
async def no_body_errors(request: Request, exc: Exception):
    # 예외 메시지에 입력값이 섞일 수 있어 내용 없이 응답하고, 로그에는 예외 종류만 남긴다.
    logging.getLogger('mirinohu').error('request failed: %s', type(exc).__name__)
    return JSONResponse({'detail': 'internal error'}, status_code=500)


@app.get('/health')
def health():
    return {'status': 'ok', 'predict': PREDICT_ON}


@app.post('/predict')
def predict(q: PredictIn):
    if not PREDICT_ON:
        raise HTTPException(503, 'model not deployed')
    return to_response(model.predict(q.model_dump()))
