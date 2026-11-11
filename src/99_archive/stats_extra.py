"""보고서용 부가 통계: 전처리 표, 변수 커버리지."""
import pandas as pd, numpy as np, pickle
from common_ml import *
S = pd.read_pickle(W + 'analytic.pkl')
rows = []
for p in PANELS:
    tr, te = split(S, p); d = S[S.panel == p]
    rows.append(dict(panel=p, name=NAME[p], rows=len(d), persons=d.pid.nunique(), years=f'{d.svy_year.min()}–{d.svy_year.max()}',
                     pos=d.y.mean(), n_tr=len(tr), pos_tr=tr.y.mean(), n_te=len(te), pos_te=te.y.mean(),
                     te_years='·'.join(str(y) for y in TEST_YEARS[p]), tr_last=tr.svy_year.max(),
                     med_ratio=d.ratio.median(), emp=d.employed.mean(), age=d.age.mean()))
T = pd.DataFrame(rows); T.to_csv(W + 'prep_table.csv', index=False); print(T.round(3).to_string())
line = pd.read_csv(W + 'poverty_line.csv'); print(line.tail())
