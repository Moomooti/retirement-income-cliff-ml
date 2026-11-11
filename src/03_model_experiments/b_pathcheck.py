"""B20: 실제 시험 행을 '화면 답'으로 되돌려 predict.py로 돌렸을 때 학습 경로와 같은 결과인지 (집계만 출력)"""
import numpy as np, pandas as pd, pickle, sys
from sklearn.metrics import roc_auc_score
from common_ml import W
sys.path.insert(0, W + 'spkg/mirisaju_model'); from predict import Model
from label_v3_fn import label
m = Model(W + 'spkg/mirisaju_model/model')
cpi = pd.read_csv('/mnt/user-data/attachments/e5872982-71a4-5f1c-953f-30befae32eac/6ab02c44-7_cpi_kosis_2020eq100.csv').set_index('year').cpi
SFp = pickle.load(open(W + 's_features.pkl', 'rb')); key = ['panel', 'pid', 'svy_year']
D0 = pd.read_pickle(W + 'v3_D0.pkl'); d = D0[(D0.panel == 'KOWEPS') & D0.age.between(50, 69)].copy()
ok, y = label(d, 'r'); d['y'] = y; d = d[ok & (d.r > 0) & (d.r < 1)]
ty = sorted(d.svy_year.unique())[-2:]; te = d[d.svy_year.isin(ty)].reset_index(drop=True)
P = pd.read_pickle(W + 'p_koweps.pkl').sort_values(['pid', 'svy_year']).drop_duplicates(['panel', 'pid', 'svy_year'])
P['hhsize'] = P.groupby('pid').hhsize.transform(lambda s: s.ffill().bfill()).fillna(2).clip(1, 10)
def lag(k, cols):
    o = P[['pid', 'svy_year'] + cols].copy(); o['svy_year'] += k; return o.rename(columns={c: f'{c}_{k}' for c in cols})
T = te[['pid', 'svy_year', 'inc_year', 'y']].merge(P[['pid', 'svy_year', 'hhdin', 'hhsize', 'age', 'female', 'married', 'edu3', 'employed', 'x_pension_recv',
     'x_retire_pension', 'x_private_pension', 'x_regular', 'x_temp_daily', 'x_selfemp', 'x_owner', 'x_fin_assets', 'x_debt']], on=['pid', 'svy_year'], how='left') \
     .merge(lag(1, ['hhdin', 'employed']), on=['pid', 'svy_year'], how='left').merge(lag(2, ['hhdin', 'employed', 'hhsize']), on=['pid', 'svy_year'], how='left')
_sf = SFp['SF']; rawreal = _sf[_sf.panel == 'KOWEPS'].set_index(['pid', 'svy_year']).s_lg_real
f = lambda v: None if pd.isna(v) else float(v)
sc, el, md = [], [], []
for _, r in T.iterrows():
    job = 'regular' if r.x_regular == 1 else 'temp' if r.x_temp_daily == 1 else 'self' if r.x_selfemp == 1 else ('other' if r.employed == 1 else 'none')
    rv = rawreal.get((r.pid, r.svy_year), 0); rv = 0 if pd.isna(rv) else rv; real25 = np.sign(rv) * np.expm1(abs(rv))
    a = dict(birth_year=int(r.inc_year - r.age), female=r.female, married=r.married, edu3=r.edu3, hh_size=r.hhsize, hh_size_2y=f(r.hhsize_2) or r.hhsize,
             pension_recv=r.x_pension_recv, retire_pension=r.x_retire_pension, private_pension=r.x_private_pension,
             income_now=r.hhdin / 12, income_1y=None if pd.isna(r.hhdin_1) else r.hhdin_1 / 12, income_2y=None if pd.isna(r.hhdin_2) else r.hhdin_2 / 12,
             employed=r.employed, employed_1y=f(r.employed_1), employed_2y=f(r.employed_2), job_type=job, owner=r.x_owner,
             fin_asset=r.x_fin_assets if pd.notna(r.x_fin_assets) else 0, debt=r.x_debt if pd.notna(r.x_debt) else 0, real_asset=real25 * cpi[r.inc_year] / cpi[2025])
    o = m.predict(a, income_year=int(r.inc_year)); el.append(o.get('eligible')); md.append(o.get('mode')); sc.append(o.get('final', np.nan))
sc = np.array(sc, float); ok = ~np.isnan(sc)
print('대상', len(T), '| below 모드로 간 비율', round(np.mean([x == 'below' for x in md]), 4), '| 점수 나온 비율', round(ok.mean(), 4))
print('화면 경로 AUC', round(roc_auc_score(T.y[ok], sc[ok]), 4), '(학습 경로 0.8132)')
