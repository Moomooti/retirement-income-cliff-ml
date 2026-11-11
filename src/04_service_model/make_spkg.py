"""미리사주 서비스 모델 패키지 + 화면→변수 경로 내부 검증"""
import numpy as np, pandas as pd, pickle, json, os, shutil, sys, joblib
from sklearn.metrics import roc_auc_score
import sklearn, lightgbm as lgb
from common_ml import W
OUT = W + 'spkg/mirisaju_model/'; shutil.rmtree(W + 'spkg', ignore_errors=True); os.makedirs(OUT + 'model')
O = pickle.load(open(W + 's_out.pkl', 'rb')); SFp = pickle.load(open(W + 's_features.pkl', 'rb'))
cpi = pd.read_csv('/mnt/user-data/attachments/e5872982-71a4-5f1c-953f-30befae32eac/6ab02c44-7_cpi_kosis_2020eq100.csv').set_index('year').cpi
G = np.linspace(0, 1, 1001)
for tag in ['S20', 'S21']:
    o = O[('KOWEPS', tag)]; M, R, ref = o['M'], o['res'], o['ref']
    M['gbm'].booster_.save_model(OUT + f'model/{tag}_lgb.txt'); M['mc'].booster_.save_model(OUT + f'model/{tag}_lgb_conformal.txt')
    joblib.dump(M['lr'], OUT + f'model/{tag}_lr.joblib')
    tr, te, _ = pickle.load(open(W + 'v3_data_KOWEPS_r.pkl', 'rb')); te = te.reset_index(drop=True).merge(SFp['SF'], on=['panel', 'pid', 'svy_year'], how='left')
    Xt = te[M['cols']].astype(float)
    for c, (lo, hi) in M['clip'].items(): Xt[c] = Xt[c].clip(lo, hi)
    sg, sl = M['gbm'].predict_proba(Xt)[:, 1], M['lr'].predict_proba(Xt)[:, 1]
    fin = (np.interp(sg, ref['g'], G) + np.interp(sl, ref['l'], G)) / 2; qf = np.quantile(fin, G)
    meta = dict(model=f'mirisaju-koweps-{tag}', features=M['cols'], clip={k: list(v) for k, v in M['clip'].items()},
                ref_quantiles=dict(lgb=ref['g'].tolist(), lr=ref['l'].tolist(), final=qf.tolist()),
                conformal=dict(q0=M['q0'], q1=M['q1'], alpha=0.10),
                test={k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in R.items() if k not in ('cols', 'params')},
                versions=dict(lightgbm=lgb.__version__, sklearn=sklearn.__version__, numpy=np.__version__, pandas=pd.__version__))
    meta['test'] = {k: (bool(v) if isinstance(v, np.bool_) else v) for k, v in meta['test'].items()}
    json.dump(meta, open(OUT + f'model/{tag}_meta.json', 'w'), ensure_ascii=False)
dl = SFp['dline']
json.dump(dict(poverty_line_2023won={int(k): float(v) for k, v in dl.items()}, cpi={int(k): float(v) for k, v in cpi.items()}, default_income_year=2025,
               note='빈곤선: 복지패널 균등화 가처분소득 가중 중위 50%(연, 만원, 2023년 가격). 2025년 이후는 2024년 값을 실질 동일로 가정. CPI는 2025년까지.'),
          open(OUT + 'model/constants.json', 'w'), ensure_ascii=False)
shutil.copy(W + 'spkg_predict.py', OUT + 'predict.py')

# ---- 내부 검증: 실제 시험 행을 '화면 답'으로 되돌려 predict.py 경로로 변수를 만들면 학습 변수와 같은가 (결과 파일은 내보내지 않음) ----
sys.path.insert(0, OUT); from predict import Model
m = Model(OUT + 'model')
P = pd.concat([pd.read_pickle(W + f'p_{p}.pkl') for p in ['koweps']]).sort_values(['pid', 'svy_year']).drop_duplicates(['panel', 'pid', 'svy_year'])
P['hhsize'] = P.groupby('pid').hhsize.transform(lambda s: s.ffill().bfill()).fillna(2).clip(1, 10)
def lag(k, cols):
    o = P[['pid', 'svy_year'] + cols].copy(); o['svy_year'] += k; return o.rename(columns={c: f'{c}_{k}' for c in cols})
tr, te, _ = pickle.load(open(W + 'v3_data_KOWEPS_r.pkl', 'rb')); te = te.reset_index(drop=True).merge(SFp['SF'], on=['panel', 'pid', 'svy_year'], how='left')
T = te[['pid', 'svy_year', 'inc_year', 'y']].merge(P[['pid', 'svy_year', 'hhdin', 'hhsize', 'age', 'female', 'married', 'edu3', 'employed', 'x_pension_recv',
             'x_retire_pension', 'x_private_pension', 'x_regular', 'x_temp_daily', 'x_selfemp', 'x_owner', 'x_fin_assets', 'x_debt', 'x_health_bad']],
             on=['pid', 'svy_year'], how='left').merge(lag(1, ['hhdin', 'employed']), on=['pid', 'svy_year'], how='left').merge(lag(2, ['hhdin', 'employed', 'hhsize']), on=['pid', 'svy_year'], how='left')
H = SFp['SF'][['panel', 'pid', 'svy_year']].copy()
_sf = SFp['SF']; rawreal = _sf[_sf.panel == 'KOWEPS'].set_index(['pid', 'svy_year']).s_lg_real
res = []; F_api = []
for i, r in T.iterrows():
    job = 'regular' if r.x_regular == 1 else 'temp' if r.x_temp_daily == 1 else 'self' if r.x_selfemp == 1 else ('other' if r.employed == 1 else 'none')
    real25 = np.sign(rawreal.get((r.pid, r.svy_year), 0)) * np.expm1(abs(rawreal.get((r.pid, r.svy_year), 0)))   # 2025년 가격 금액 복원
    f = lambda v: None if pd.isna(v) else float(v)
    a = dict(birth_year=int(r.inc_year - r.age), female=r.female, married=r.married, edu3=r.edu3, hh_size=r.hhsize, hh_size_2y=f(r.hhsize_2) or r.hhsize,
             pension_recv=r.x_pension_recv, retire_pension=r.x_retire_pension, private_pension=r.x_private_pension,
             income_now=r.hhdin / 12, income_1y=None if pd.isna(r.hhdin_1) else r.hhdin_1 / 12, income_2y=None if pd.isna(r.hhdin_2) else r.hhdin_2 / 12,
             employed=r.employed, employed_1y=f(r.employed_1), employed_2y=f(r.employed_2), job_type=job, owner=r.x_owner,
             fin_asset=r.x_fin_assets if pd.notna(r.x_fin_assets) else 0,
             debt=r.x_debt if pd.notna(r.x_debt) else 0, real_asset=real25 * cpi[r.inc_year] / cpi[2025])
    F, _ = m.features(a, income_year=int(r.inc_year)); F_api.append(F)
F_api = pd.DataFrame(F_api)
cols = O[('KOWEPS', 'S20')]['M']['cols']
cmp = {}
for c in cols:
    x, z = te[c].astype(float).values, F_api[c].astype(float).values; both = ~(np.isnan(x) & np.isnan(z))
    cmp[c] = float(np.mean(np.isclose(x[both], z[both], atol=1e-6, equal_nan=False))) if both.any() else 1.0
print('변수별 일치율(학습 변수 vs 화면 경로):'); print({k: round(v, 4) for k, v in cmp.items() if v < 0.9999})
M = O[('KOWEPS', 'S20')]['M']; ref = O[('KOWEPS', 'S20')]['ref']
def sc(X):
    X = X[cols].astype(float).copy()
    for c, (lo, hi) in M['clip'].items(): X[c] = X[c].clip(lo, hi)
    return (np.interp(M['gbm'].predict_proba(X)[:, 1], ref['g'], G) + np.interp(M['lr'].predict_proba(X)[:, 1], ref['l'], G)) / 2
a1, a2 = sc(te), sc(F_api)
print('AUC 학습 변수', roc_auc_score(te.y, a1), ' 화면 경로', roc_auc_score(te.y, a2), ' 점수 상관', np.corrcoef(a1, a2)[0, 1], ' 상위20% 일치', np.mean((a1 >= np.quantile(a1, .8)) == (a2 >= np.quantile(a2, .8))))
pickle.dump(dict(cmp=cmp, auc_train=roc_auc_score(te.y, a1), auc_api=roc_auc_score(te.y, a2), corr=np.corrcoef(a1, a2)[0, 1]), open(W + 's_pathcheck.pkl', 'wb'))
