"""CPI 기준연도 2023 → 2025 변경 검증 (팀 환경에서 원자료로 실행).

사전 등록 기준 (실행 전에 고정, 결과가 나빠도 그대로 보고)
  C1  정답(지속 하락 여부)이 모든 행에서 같다                 (불일치 0행)
  C2  빈곤선 대비 비율 변수가 같다                             (최대 차이 < 1e-9)
  C3  금액 변수는 정확히 CPI 배수만큼 커진다                    (116.61/111.59, 상대 오차 < 1e-9)
  C4  과제별 시험 AUC 차이 |새 − 옛| ≤ 0.002, 판정(+0.064 [하한 > 0, ≥ +0.03, 3/3])이 바뀌지 않는다

사용법
  python check_cpi_2025.py OLD.csv NEW.csv --key panel pid year --label y \
      --ratio log_ratio log_dratio min_ratio_hist d_log_ratio_2y \
      --money x_own_earn_l2 --score score --test-col is_test
  (OLD/NEW = 2023 가격 / 2025 가격으로 만든 분석 데이터. --score는 각 파일에 그 데이터로 다시 학습한 최종 모델 점수 열.
   열 이름은 팀 파이프라인에 맞게 바꾸기)
"""
import argparse
import sys

import numpy as np
import pandas as pd

K = 116.61 / 111.59

ap = argparse.ArgumentParser()
ap.add_argument('old'); ap.add_argument('new')
ap.add_argument('--key', nargs='+', required=True)
ap.add_argument('--label', required=True)
ap.add_argument('--ratio', nargs='*', default=[])
ap.add_argument('--money', nargs='*', default=[])
ap.add_argument('--score'); ap.add_argument('--test-col')
a = ap.parse_args()

o, n = pd.read_csv(a.old), pd.read_csv(a.new)
d = o.merge(n, on=a.key, suffixes=('_o', '_n'), validate='one_to_one')
ok = True
print(f'행 수: 옛 {len(o):,} / 새 {len(n):,} / 연결 {len(d):,}')
ok &= len(d) == len(o) == len(n)

bad = (d[a.label + '_o'] != d[a.label + '_n']).sum()
print(f'C1 정답 불일치 {bad}행'); ok &= bad == 0
for c in a.ratio:
    diff = (d[c + '_o'] - d[c + '_n']).abs().max()
    print(f'C2 {c}: 최대 차이 {diff:.2e}'); ok &= not (diff >= 1e-9)
for c in a.money:
    x, y = d[c + '_o'], d[c + '_n']; m = x.abs() > 0
    rel = ((y[m] / x[m]) / K - 1).abs().max() if m.any() else 0.0
    print(f'C3 {c}: 배수 오차 {rel:.2e}'); ok &= not (rel >= 1e-9)
if a.score:
    from sklearn.metrics import roc_auc_score
    t = d[d[a.test_col + '_o'] == 1] if a.test_col else d
    yv = t[a.label + '_o']
    ao, an = roc_auc_score(yv, t[a.score + '_o']), roc_auc_score(yv, t[a.score + '_n'])
    print(f'C4 시험 AUC: 옛 {ao:.4f} / 새 {an:.4f} / 차이 {an - ao:+.4f}'); ok &= abs(an - ao) <= 0.002
print('결과:', '통과' if ok else '미달 – 원인 확인 후 보고서에 그대로 기록')
sys.exit(0 if ok else 1)
