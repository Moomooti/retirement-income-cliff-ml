import numpy as np, pandas as pd, warnings
from common_ml import *
from sklearn.metrics import roc_auc_score
import lightgbm as lgb
warnings.filterwarnings('ignore')
SA = pd.read_pickle(W + 'analytic_all.pkl'); SA = SA[SA.ratio_f4.notna() & (SA.ratio >= 1)].copy()
SA['y'] = ((SA.ratio_f2 < 1) & (SA.ratio_f4 < 1)).astype(int)
TR, TE = [], []
for p in PANELS:
    d = SA[SA.panel == p]; ty = sorted(d.svy_year.unique())[-2:]
    TE.append(d[d.svy_year.isin(ty)]); TR.append(d[d.svy_year <= min(ty) - 4])
tr, te = pd.concat(TR), pd.concat(TE)
ex = sorted(set(sum([extra_features(t.copy()) for t in TR], [])))
for D in (tr, te):
    for c in ex:
        if c.startswith('lg_') and c not in D: D[c] = np.sign(D[c[3:]]) * np.log1p(np.abs(D[c[3:]]))
    for p in PANELS: D['pn_' + p] = (D.panel == p).astype(int)
for name, cols in [('common', COMMON + ['pn_' + p for p in PANELS]), ('full', COMMON + ex + ['pn_' + p for p in PANELS])]:
    m = lgb.LGBMClassifier(n_estimators=700, learning_rate=0.03, num_leaves=31, min_child_samples=100, subsample=0.8, subsample_freq=1,
                           colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=42).fit(tr[cols].astype(float), tr.y)
    te['s'] = m.predict_proba(te[cols].astype(float))[:, 1]
    print(name, {p: round(roc_auc_score(g.y, g.s), 3) for p, g in te.groupby('panel')}, 'mean', round(np.mean([roc_auc_score(g.y, g.s) for _, g in te.groupby('panel')]), 3))
for lo, hi in [(55, 64)]:
    t = te[te.age.between(lo, hi)]
    print('age', lo, hi, {p: round(roc_auc_score(g.y, g.s), 3) for p, g in t.groupby('panel')}, {p: round(roc_auc_score(g.y, -g.log_ratio), 3) for p, g in t.groupby('panel')})
