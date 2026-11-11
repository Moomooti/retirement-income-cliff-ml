"""일치 테스트: 화면 입력(합성 300건) → predict.py 결과가 학습 환경 점수와 같은지. 실행: python test_parity.py"""
import os, json, numpy as np, pandas as pd
from predict import Model
HERE = os.path.dirname(os.path.abspath(__file__))


def test_parity():
    m = Model(os.path.join(HERE, 'model')); d = pd.read_csv(os.path.join(HERE, 'parity_cases.csv')); bad = 0
    for _, r in d.iterrows():
        o = m.predict(json.loads(r.input))
        assert o['eligible'] == bool(r.expected_eligible), '대상 판정 불일치'
        if o['eligible']:
            bad += abs(o['lgb'] - r.expected_lgb) > 1e-6 or abs(o['lr'] - r.expected_lr) > 1e-6 or abs(o['top_pct'] - r.expected_top_pct) > 1e-4
    assert bad == 0, f'{bad}건 불일치'
    print(f'통과: {len(d)}건 (대상 {int(d.expected_eligible.sum())}건 점수 일치)')


if __name__ == '__main__':
    test_parity()
