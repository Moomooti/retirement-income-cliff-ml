"""E4 확률 보정 개선 (prereg_E124.txt)"""
import numpy as np, pandas as pd, pickle, warnings, ast
from common_ml import *
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
import lightgbm as lgb
warnings.filterwarnings('ignore')
O = pickle.load(open(W + 'v3_out.pkl', 'rb')); TU = pd.DataFrame(O['tune'])
TASKS = [('KOWEPS', 'r'), ('NaSTaB', 'r'), ('KReIS', 'r'), ('KReIS', 'rn'), ('KLIPS', 'r')]
lg_ = lambda q: np.log(np.clip(q, 1e-4, 1 - 1e-4) / (1 - np.clip(q, 1e-4, 1 - 1e-4)))
def ece(q, y):
    b = pd.qcut(q, 10, labels=False, duplicates='drop'); return sum(abs(q[b == i].mean() - y[b == i].mean()) * (b == i).mean() for i in np.unique(b))
rows = []
for p, base in TASKS:
    k = f'{p}_{base}'; tr, te, cols = pickle.load(open(W + f'v3_data_{p}_{base}.pkl', 'rb')); tr, te = tr.reset_index(drop=True), te.reset_index(drop=True)
    X, Xt = tr[cols].astype(float), te[cols].astype(float)
    for c in X.columns:
        if c in CATEG or X[c].nunique() <= 3: continue
        lo, hi = X[c].quantile([0.005, 0.995]); X[c] = X[c].clip(lo, hi); Xt[c] = Xt[c].clip(lo, hi)
    y, yt = tr.y.values, te.y.values
    t = TU[(TU.task == k) & (TU.model == 'LightGBM')].iloc[0]; prm = t.params if isinstance(t.params, dict) else ast.literal_eval(t.params)
    mk = lambda n=int(t.iters): lgb.LGBMClassifier(n_estimators=n, learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=42, **prm)
    q = mk().fit(X, y).predict_proba(Xt)[:, 1]
    # B: 기존 – 학습구간 앞부분 학습 → 마지막 2개 연도 예측으로 Platt
    vy = sorted(tr.svy_year.unique())[-2:]; iv = tr.svy_year.isin(vy).values; it = (tr.svy_year <= min(vy) - 4).values
    qi = mk().fit(X[it], y[it]).predict_proba(X[iv])[:, 1]
    qB = LogisticRegression().fit(lg_(qi).reshape(-1, 1), y[iv]).predict_proba(lg_(q).reshape(-1, 1))[:, 1]
    # C: 사람 단위 5겹 교차 예측 → Platt
    oof = np.zeros(len(tr))
    for a_, b_ in GroupKFold(5).split(X, y, tr.pid): oof[b_] = mk().fit(X.iloc[a_], y[a_]).predict_proba(X.iloc[b_])[:, 1]
    qC = LogisticRegression().fit(lg_(oof).reshape(-1, 1), y).predict_proba(lg_(q).reshape(-1, 1))[:, 1]
    for nm, qq in [('A 원 확률', q), ('B 마지막 연도 Platt', qB), ('C 교차 예측 Platt', qC)]:
        rows.append(dict(task=k, method=nm, ece=ece(qq, yt), citl=abs(qq.mean() - yt.mean()), mean_pred=qq.mean(), obs=yt.mean(), brier=brier_score_loss(yt, qq)))
    print(k, {r['method'][:1]: round(r['ece'] * 100, 2) for r in rows[-3:]}, flush=True)
R = pd.DataFrame(rows)
piv = R.pivot(index='task', columns='method', values='ece')
c_best = (piv['C 교차 예측 Platt'] <= piv.min(axis=1) + 1e-12).sum()
c_worse = ((piv['C 교차 예측 Platt'] - piv['A 원 확률']) > 0.01).sum()
verdict = '채택' if (c_best >= 4 and c_worse == 0) else '불채택'
print((piv * 100).round(2)); print('C 최저', c_best, '/5 · A보다 1%p 넘게 나쁜 과제', c_worse, '→', verdict)
pickle.dump(dict(R=R, verdict=verdict, c_best=int(c_best), c_worse=int(c_worse)), open(W + 'e4_out.pkl', 'wb'))
