import numpy as np, pandas as pd, pickle, warnings
from common_ml import *
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score
import lightgbm as lgb
warnings.filterwarnings('ignore')
PS = ['KOWEPS', 'NaSTaB', 'KReIS', 'KLIPS']
D = {p: pickle.load(open(W + f'v3_data_{p}_r.pkl', 'rb')) for p in PS}
cols = sorted(set(sum([D[p][2] for p in PS], [])))
tr = pd.concat([D[p][0] for p in PS]); te = pd.concat([D[p][1] for p in PS])
for X in (tr, te):
    X['log_cur'] = np.where(X.panel == 'KLIPS', X.log_ratio, X.log_dratio)
    for p in PS: X['pn_' + p] = (X.panel == p).astype(int)
cols = [c for c in cols if c in tr] + ['log_cur'] + ['pn_' + p for p in PS]
m = lgb.LGBMClassifier(n_estimators=900, learning_rate=0.03, num_leaves=31, min_child_samples=80, subsample=0.8, subsample_freq=1,
                       colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=42).fit(tr[cols].astype(float), tr.y)
te['s'] = m.predict_proba(te[cols].astype(float))[:, 1]
pr = pickle.load(open(W + 'label_v3_preds.pkl', 'rb'))
for p in PS:
    g = te[te.panel == p]; own = [v for k, v in pr.items() if k[0] == p][0]
    ens = rankdata(g.s.values) + rankdata(own.ml.values) + rankdata(own.lr.values)
    print(p, 'pooled', round(roc_auc_score(g.y, g.s), 3), 'own ML', round(roc_auc_score(own.y, own.ml), 3), 'pooled+own+LR', round(roc_auc_score(g.y, ens), 3))
