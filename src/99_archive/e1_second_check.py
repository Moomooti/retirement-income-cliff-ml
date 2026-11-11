"""E1 노후 계산의 2차 검진 (prereg_E124.txt)"""
import numpy as np, pandas as pd, pickle, warnings
from scipy.stats import rankdata
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
d = D0[(D0.panel == 'KReIS') & D0.age.between(50, 69) & D0.rn.notna()].copy()
f = {k: d[f'rn_f{k}'] for k in [2, 3, 4]}
ok = f[2].notna() & f[4].notna()
below = sum((f[k] < 1).astype(int) for k in f)
d['y'] = np.where(f[3].notna(), below >= 2, (f[2] < 1) & (f[4] < 1)).astype(int)
d = d[ok].copy(); d['calc_ok'] = (d.rn >= 1).astype(int)
ys = sorted(d.svy_year.unique()); ty = ys[-2:]
te = d[d.svy_year.isin(ty)].copy(); tr = d[d.svy_year <= min(ty) - 4].copy()
EX = extra_features(tr); te = add_logs(te, EX)
cols = COMMON + EX + [c for c in ['log_dratio', 'd_log_dratio_2y', 'log_rneed'] if tr[c].notna().mean() > 0.2]
cols = list(dict.fromkeys(cols))
X, Xt, y = tr[cols].astype(float), te[cols].astype(float), tr.y.values
vy = sorted(tr.svy_year.unique())[-2:]; iv = tr.svy_year.isin(vy).values; it = (tr.svy_year <= min(vy) - 4).values
best = None
for g in [dict(num_leaves=n, min_child_samples=m) for n in (15, 31) for m in (40, 150)]:
    m = lgb.LGBMClassifier(n_estimators=3000, learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=42, **g)
    m.fit(X[it], y[it], eval_set=[(X[iv], y[iv])], eval_metric='auc', callbacks=[lgb.early_stopping(100, verbose=False)])
    a = roc_auc_score(y[iv], m.predict_proba(X[iv])[:, 1])
    if best is None or a > best[0]: best = (a, g, m.best_iteration_)
mkL = lambda: lgb.LGBMClassifier(n_estimators=max(50, int(best[2] * 1.1)), learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=42, **best[1])
mkR = lambda: make_pipeline(SimpleImputer(add_indicator=True), StandardScaler(), LogisticRegression(max_iter=3000))
# 학습셋 OOF 점수 → 위험 구간 경계
oof_l, oof_r = np.zeros(len(tr)), np.zeros(len(tr))
for a_, b_ in GroupKFold(5).split(X, y, tr.pid):
    oof_l[b_] = mkL().fit(X.iloc[a_], y[a_]).predict_proba(X.iloc[b_])[:, 1]
    oof_r[b_] = mkR().fit(X.iloc[a_], y[a_]).predict_proba(X.iloc[b_])[:, 1]
# 순위 평균은 집합마다 스케일이 달라서, 학습 OOF 분포 기준 백분위로 변환해 같은 척도에 놓는다
def pct_of(ref, v): return np.searchsorted(np.sort(ref), v, side='right') / len(ref)
oof_s = (pct_of(oof_l, oof_l) + pct_of(oof_r, oof_r)) / 2
L, R = mkL().fit(X, y), mkR().fit(X, y)
te_s = (pct_of(oof_l, L.predict_proba(Xt)[:, 1]) + pct_of(oof_r, R.predict_proba(Xt)[:, 1])) / 2
c50, c80 = np.quantile(oof_s, 0.5), np.quantile(oof_s, 0.8)
te['tier'] = np.select([te_s >= c80, te_s >= c50], ['높음', '중간'], '낮음'); te['score'] = te_s
def wilson(k, n, z=1.96):
    if n == 0: return (np.nan, np.nan, np.nan)
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, c - h, c + h
rows = []
for calc in [1, 0]:
    for tier in ['낮음', '중간', '높음', '전체']:
        s = te[(te.calc_ok == calc) & ((te.tier == tier) | (tier == '전체'))]
        p, lo, hi = wilson(int(s.y.sum()), len(s))
        rows.append(dict(calc='계산상 괜찮음' if calc else '계산상 부족', tier=tier, n=len(s), falls=int(s.y.sum()), rate=p, lo=lo, hi=hi))
Q = pd.DataFrame(rows); print(Q.round(3).to_string())
g = te[te.calc_ok == 1]
A_, B_, dl, se, pv_, _ = delong_diff(g.y.values, g.score.values, -g.log_rneed.values)
gr = {r.tier: r for r in Q[Q.calc == '계산상 괜찮음'].itertuples()}
mono = gr['낮음'].rate < gr['중간'].rate < gr['높음'].rate; sep = gr['높음'].lo > gr['낮음'].hi
verdict = '성공' if (mono and sep) else '실패'
print('계산상 괜찮음 안: 충족률 AUC', round(B_, 3), 'ML', round(A_, 3), 'Δ', round(dl, 3), 'p', pv_, '| 순서', mono, '분리', sep, '→', verdict)
print('전체 시험', len(te), '계산상 괜찮음', len(g), '그중 반복 부족', round(g.y.mean(), 3))
pickle.dump(dict(Q=Q, auc_ml=A_, auc_calc=B_, delta=dl, se=se, p=pv_, verdict=verdict, mono=mono, sep=sep, n_te=len(te), n_ok=len(g),
                 ok_rate=g.y.mean(), cut=(c50, c80), te_years=ty, n_tr=len(tr), inner=best[0]), open(W + 'e1_out.pkl', 'wb'))
