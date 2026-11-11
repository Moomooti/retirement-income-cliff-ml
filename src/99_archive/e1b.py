import numpy as np, pandas as pd, pickle, warnings
from common_ml import *
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import lightgbm as lgb
warnings.filterwarnings('ignore')
D0 = pd.read_pickle(W + 'v3_D0.pkl')
d = D0[(D0.panel == 'KReIS') & D0.age.between(50, 69) & D0.rn.notna() & (D0.rn >= 1)].copy()
f = {k: d[f'rn_f{k}'] for k in [2, 3, 4]}; ok = f[2].notna() & f[4].notna(); below = sum((f[k] < 1).astype(int) for k in f)
d['y'] = np.where(f[3].notna(), below >= 2, (f[2] < 1) & (f[4] < 1)).astype(int); d = d[ok].copy()
pct_of = lambda ref, v: np.searchsorted(np.sort(ref), v, side='right') / len(ref)
ORIG = {'O1': [2013, 2015], 'O2': [2015, 2017], 'O3(사후)': [2017, 2019]}
res, allte = [], []
for on, ty in ORIG.items():
    te = d[d.svy_year.isin(ty)].copy(); tr = d[d.svy_year <= min(ty) - 4].copy()
    EX = extra_features(tr); te = add_logs(te, EX)
    cols = list(dict.fromkeys(COMMON + EX + [c for c in ['log_dratio', 'd_log_dratio_2y', 'log_rneed'] if tr[c].notna().mean() > 0.2]))
    X, Xt, y = tr[cols].astype(float), te[cols].astype(float), tr.y.values
    mkL = lambda: lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=80, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=2, random_state=42)
    mkR = lambda: make_pipeline(SimpleImputer(add_indicator=True), StandardScaler(), LogisticRegression(max_iter=3000, C=0.3))
    oL, oR = np.zeros(len(tr)), np.zeros(len(tr))
    for a, b in GroupKFold(5).split(X, y, tr.pid):
        oL[b] = mkL().fit(X.iloc[a], y[a]).predict_proba(X.iloc[b])[:, 1]; oR[b] = mkR().fit(X.iloc[a], y[a]).predict_proba(X.iloc[b])[:, 1]
    oof = (pct_of(oL, oL) + pct_of(oR, oR)) / 2
    s = (pct_of(oL, mkL().fit(X, y).predict_proba(Xt)[:, 1]) + pct_of(oR, mkR().fit(X, y).predict_proba(Xt)[:, 1])) / 2
    c70, c90 = np.quantile(oof, 0.7), np.quantile(oof, 0.9)
    te['ml'] = s; te['calc'] = -te.log_rneed; te['origin'] = on
    te['tier'] = np.select([s >= c90, s >= c70], ['상위 10%', '10~30%'], '나머지 70%')
    yt = te.y.values; r = dict(origin=on, years='·'.join(map(str, ty)), n_tr=len(tr), n_te=len(te), falls=int(yt.sum()), rate=yt.mean(),
                               auc_ml=roc_auc_score(yt, s), auc_calc=roc_auc_score(yt, te.calc))
    for q in [0.1, 0.2]:
        k = int(round(len(te) * q)); r[f'k{int(q*100)}'] = k
        r[f'ml{int(q*100)}'] = int(yt[np.argsort(-s)[:k]].sum()); r[f'calc{int(q*100)}'] = int(yt[np.argsort(-te.calc.values)[:k]].sum())
    for t in ['상위 10%', '10~30%', '나머지 70%']:
        g = te[te.tier == t]; r[f'n_{t}'] = len(g); r[f'rate_{t}'] = g.y.mean() if len(g) else np.nan
    res.append(r); allte.append(te[['origin', 'pid', 'y', 'ml', 'calc']]); print(r, flush=True)
R = pd.DataFrame(res); A = pd.concat(allte)
# 합친 사람 단위 부트스트랩: 시점별 상위 20% 선택 차이(ML − 충족률)의 합
def found_diff(df):
    tot = 0
    for on, g in df.groupby('origin'):
        k = int(round(len(g) * 0.2)); y = g.y.values
        tot += y[np.argsort(-g.ml.values)[:k]].sum() - y[np.argsort(-g.calc.values)[:k]].sum()
    return tot
rng = np.random.RandomState(42); pids = A.pid.unique(); idx = A.groupby('pid').indices; bs = []
for _ in range(1000):
    ii = np.concatenate([idx[p] for p in rng.choice(pids, len(pids))]); bs.append(found_diff(A.iloc[ii]))
est = found_diff(A); lo, hi = np.percentile(bs, [2.5, 97.5])
allwin = bool(((R.ml10 > R.calc10) & (R.ml20 > R.calc20)).all())
mono = bool(((R['rate_상위 10%'] > R['rate_10~30%']) & (R['rate_10~30%'] > R['rate_나머지 70%'])).all())
verdict = '성공' if (allwin and lo > 0) else '실패'
print('합친 차이(20%)', est, [lo, hi], '모든 시점 ML 우세', allwin, '구간 순서', mono, '→', verdict)
pickle.dump(dict(R=R, est=est, lo=lo, hi=hi, allwin=allwin, mono=mono, verdict=verdict), open(W + 'e1b_out.pkl', 'wb'))
