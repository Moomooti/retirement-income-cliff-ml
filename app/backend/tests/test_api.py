"""API 테스트: 실행 `python -m pytest -q tests` (backend 폴더에서)

1) API 일치: 합성 화면 입력 300건을 HTTP /predict 로 넣은 결과 = 모델 패키지 기대값 (대상 판정·순위·판단 보류)
2) 계약: 응답 형식(mode·feature 포함), 대상 아님(나이·소득 0), 기준선 아래(B20), 입력 검증, CORS
3) 로그 원칙: 요청 본문이 로그에 남지 않음
"""
import json
import logging
import os

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app

HERE = os.path.dirname(os.path.abspath(__file__))
client = TestClient(app)
EXAMPLE = dict(birth_year=1964, female=0, married=1, edu3=1, hh_size=2, hh_size_2y=3,
               pension_recv=0, retire_pension=1, private_pension=0,
               income_now=280, income_1y=330, income_2y=400,
               employed=0, employed_1y=1, employed_2y=1, job_type='none',
               owner=1, fin_asset=3000, real_asset=35000, debt=4000)


def test_api_parity():
    d = pd.read_csv(os.path.join(HERE, 'parity_cases.csv'))
    for _, r in d.iterrows():
        a = json.loads(r.input)
        res = client.post('/predict', json=a)
        assert res.status_code == 200, (res.status_code, res.text)
        j = res.json()
        assert j['eligible'] == bool(r.expected_eligible)
        if j['eligible']:
            assert abs(j['top_pct'] - r.expected_top_pct) <= 0.05 + 1e-9     # 응답은 소수 1자리로 반올림
            ab = r.get('expected_abstain')                                     # 패키지 CSV에는 이 열이 없거나 비어 있음 → 값이 있을 때만 비교
            if ab is not None and pd.notna(ab):
                assert j['abstain'] == bool(ab)


def test_predict_contract():
    j = client.post('/predict', json=EXAMPLE).json()
    assert j['eligible'] is True and j['band'] in ('high', 'mid', 'low') and 0 <= j['top_pct'] <= 100
    assert isinstance(j['abstain'], bool) and 1 <= len(j['reasons']) <= 3
    assert all(set(x) == {'feature', 'label', 'effect'} for x in j['reasons']) and 'lgb' not in j and 'lr' not in j
    assert j['mode'] == 'above'
    assert j['model']['version'] and j['model']['note']


def test_health_model_switch():
    a = client.post('/predict', json=EXAMPLE).json()['model']['version']
    b = client.post('/predict', json={**EXAMPLE, 'health': 4}).json()['model']['version']
    assert a != b                                      # 건강 답하면 S21, 없으면 S20


@pytest.mark.parametrize('change, word', [(dict(birth_year=1990), '50~69세'), (dict(income_now=0), '0보다')])
def test_not_eligible(change, word):
    j = client.post('/predict', json={**EXAMPLE, **change}).json()
    assert j['eligible'] is False and word in j['reason'] and 'band' not in j


def test_below_line_b20():
    # 지금 기준선 아래 → '대상 아님'이 아니라 B20(2년 뒤에도 아래에 머물까) 결과
    j = client.post('/predict', json={**EXAMPLE, 'income_now': 60, 'income_1y': 60, 'income_2y': 60}).json()
    assert j['eligible'] is True and j['mode'] == 'below' and j['model']['version'] == 'mirisaju-koweps-B20'
    assert j['band'] in ('high', 'mid', 'low') and 0 <= j['top_pct'] <= 100 and 1 <= len(j['reasons']) <= 3


@pytest.mark.parametrize('bad', [dict(job_type='retired'), dict(female=2), dict(health=6), dict(debt=-1),
                                 dict(edu3=3), dict(extra_field=1), dict(hh_size=0)])
def test_rejects_bad_input(bad):
    assert client.post('/predict', json={**EXAMPLE, **bad}).status_code == 422


def test_missing_field():
    a = dict(EXAMPLE); a.pop('debt')
    assert client.post('/predict', json=a).status_code == 422


def test_health_endpoint():
    assert client.get('/health').json() == {'status': 'ok', 'predict': True}


def test_cors():
    ok = client.options('/predict', headers={'Origin': 'https://mirinohulab.github.io', 'Access-Control-Request-Method': 'POST'})
    assert ok.headers.get('access-control-allow-origin') == 'https://mirinohulab.github.io'
    bad = client.options('/predict', headers={'Origin': 'https://evil.example', 'Access-Control-Request-Method': 'POST'})
    assert 'access-control-allow-origin' not in bad.headers


def test_no_body_in_logs(caplog):
    marker = 98765
    with caplog.at_level(logging.DEBUG):
        client.post('/predict', json={**EXAMPLE, 'fin_asset': marker})
        client.post('/predict', json={**EXAMPLE, 'fin_asset': marker, 'job_type': 'bad'})
    assert str(marker) not in caplog.text
