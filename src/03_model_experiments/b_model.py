"""미리사주 서비스 모델 (prereg_S.txt)"""
import numpy as np, pandas as pd, pickle, glob, warnings, time, sys
from common_ml import *
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import lightgbm as lgb
warnings.filterwarnings('ignore')
RS = 42
cpi = pd.read_csv('/mnt/user-data/attachments/e5872982-71a4-5f1c-953f-30befae32eac/6ab02c44-7_cpi_kosis_2020eq100.csv').set_index('year').cpi
defl23 = cpi[2023] / cpi; to25 = cpi[2025] / cpi
key = ['panel', 'pid', 'svy_year']

BASE = ['age', 'age_to_60', 'age_to_nps', 'female', 'married', 'edu3', 'hhsize', 's_hhchg', 'x_pension_recv',
        'x_retire_pension', 'x_private_pension', 's_log_r', 's_d1', 's_d2', 's_min3', 's_vol3', 'employed', 's_emp_l1', 's_emp_l2',
        's_lost', 'x_regular', 'x_temp_daily', 'x_selfemp', 's_owner', 's_fin_r', 's_debt_r', 's_real_r', 's_lg_fin', 's_lg_debt', 's_lg_real']
SETS = {'S20': BASE, 'S21': BASE + ['s_health']}


def winsor(X, Xt):
    X, Xt = X.copy(), Xt.copy(); clip = {}
    for c in X.columns:
        if X[c].nunique() <= 3: continue
        lo, hi = X[c].quantile([0.005, 0.995]); clip[c] = (float(lo), float(hi)); X[c] = X[c].clip(lo, hi); Xt[c] = Xt[c].clip(lo, hi)
    return X, Xt, clip


def fit_set(tr, te, cols):
    X, Xt, clip = winsor(tr[cols].astype(float), te[cols].astype(float)); y = tr.y.values
    vy = sorted(tr.svy_year.unique())[-2:]; iv = tr.svy_year.isin(vy).values; it = (tr.svy_year <= min(vy) - 4).values
    best = None
    for g in [dict(num_leaves=n, min_child_samples=m) for n in (15, 31) for m in (40, 150)]:
        m = lgb.LGBMClassifier(n_estimators=3000, learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                               verbose=-1, n_jobs=2, random_state=RS, **g)
        m.fit(X[it], y[it], eval_set=[(X[iv], y[iv])], eval_metric='auc', callbacks=[lgb.early_stopping(100, verbose=False)])
        a = roc_auc_score(y[iv], m.predict_proba(X[iv])[:, 1])
        if best is None or a > best[0]: best = (a, g, m.best_iteration_)
    n = max(50, int(best[2] * 1.1))
    mk = lambda: lgb.LGBMClassifier(n_estimators=n, learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                                    verbose=-1, n_jobs=2, random_state=RS, **best[1])
    gbm = mk().fit(X, y)
    lrm = make_pipeline(SimpleImputer(strategy='median', add_indicator=True), StandardScaler(), LogisticRegression(C=1.0, max_iter=3000)).fit(X, y)
    # 판단 보류(보고서 M-C 방식): 학습 앞부분 모델 + 내부 검증 보정
    mc = mk().fit(X[it], y[it]); sc = mc.predict_proba(X[iv])[:, 1]; yc = y[iv]
    q1 = np.quantile(1 - sc[yc == 1], np.ceil(0.9 * ((yc == 1).sum() + 1)) / (yc == 1).sum(), method='higher')
    q0 = np.quantile(sc[yc == 0], np.ceil(0.9 * ((yc == 0).sum() + 1)) / (yc == 0).sum(), method='higher')
    return dict(gbm=gbm, lr=lrm, clip=clip, cols=cols, params=best[1], iters=n, inner=best[0], mc=mc, q1=float(q1), q0=float(q0))


def score(M, te_df, ref=None):
    Xt = te_df[M['cols']].astype(float).copy()
    for c, (lo, hi) in M['clip'].items(): Xt[c] = Xt[c].clip(lo, hi)
    sg = M['gbm'].predict_proba(Xt)[:, 1]; sl = M['lr'].predict_proba(Xt)[:, 1]
    G = np.linspace(0, 1, 1001)
    if ref is None: ref = dict(g=np.quantile(sg, G), l=np.quantile(sl, G))
    fin = (np.interp(sg, ref['g'], G) + np.interp(sl, ref['l'], G)) / 2
    return sg, sl, fin, ref, Xt


def boot_diff(y, a, b, pid, B=1000, seed=42):
    rng = np.random.RandomState(seed); up = np.unique(pid); grp = pd.Series(np.arange(len(y))).groupby(pid).apply(np.array).to_dict(); out = []
    for _ in range(B):
        ii = np.concatenate([grp[u] for u in rng.choice(up, len(up))])
        if 0 < y[ii].sum() < len(ii): out.append(roc_auc_score(y[ii], a[ii]) - roc_auc_score(y[ii], b[ii]))
    return np.mean(out), np.percentile(out, 2.5), np.percentile(out, 97.5)



SFp = pickle.load(open(W + 's_features.pkl', 'rb')); SF = SFp['SF']
D0 = pd.read_pickle(W + 'v3_D0.pkl')
from label_v3_fn import label
d = D0[(D0.panel == 'KOWEPS') & D0.age.between(50, 69)].copy()
ok, y = label(d, 'r'); d['y'] = y
d = d[ok & (d.r > 0) & (d.r < 1)]                       # 지금 기준선 아래
ys = sorted(d.svy_year.unique()); ty = ys[-2:]
te = d[d.svy_year.isin(ty)].copy().reset_index(drop=True); tr = d[d.svy_year <= min(ty) - 4].copy().reset_index(drop=True)
tr = tr.merge(SF, on=key, how='left', validate='1:1'); te = te.merge(SF, on=key, how='left', validate='1:1')
print('시험 연도', ty, '| 학습', len(tr), '시험', len(te), '| 시험 머묾 비율', round(te.y.mean(), 3), '| 시험 정답 수 (머묾, 올라섬)', int(te.y.sum()), int((1 - te.y).sum()), flush=True)
print('r 일치 확인', float(np.nanmax(np.abs(np.log(te.r_chk) - np.log(te.r)))), flush=True)
C1 = len(tr) >= 1500 and len(te) >= 500 and min(te.y.sum(), (1 - te.y).sum()) >= 100
cols = [c for c in SETS['S20'] if c in tr and tr[c].notna().mean() > 0.2 and tr[c].nunique() > 1]
M = fit_set(tr, te, cols); sg, sl, fin, ref, Xt = score(M, te)
yt = te.y.values; b0 = -te.s_log_r.values; pid = te.pid.values
A_, B_, dd, se, pv, _ = delong_diff(yt, fin, b0)
C2 = dd - 1.96 * se > 0
s_c = M['mc'].predict_proba(Xt)[:, 1]; inc1 = (1 - s_c) <= M['q1']; inc0 = s_c <= M['q0']
cov_pos, cov_neg, abst = float(inc1[yt == 1].mean()), float(inc0[yt == 0].mean()), float((inc1 & inc0).mean())
C3 = cov_pos >= .85 and cov_neg >= .85
bm, blo, bhi = boot_diff(yt, fin, b0, pid)
G = np.linspace(0, 1, 1001); qf = np.quantile(fin, G); top = (1 - np.interp(fin, qf, G)) * 100
bins = [0, 20, 40, 60, 80, 100.01]; rows = []
for a_, b_ in zip(bins[:-1], bins[1:]):
    m = (top >= a_) & (top < b_); rows.append(dict(lo=a_, hi=min(b_, 100), n=int(m.sum()), stay=float(yt[m].mean())))
R = dict(test_years=ty, n_tr=len(tr), n_te=len(te), stay_rate=float(yt.mean()), n_stay=int(yt.sum()), n_up=int((1 - yt).sum()),
         auc_model=A_, auc_b0=B_, auc_lgb=roc_auc_score(yt, sg), auc_lr=roc_auc_score(yt, sl), delta=dd, delta_lo=dd - 1.96 * se, p=pv,
         boot=(bm, blo, bhi), cov_pos=cov_pos, cov_neg=cov_neg, abstain=abst, C1=bool(C1), C2=bool(C2), C3=bool(C3),
         inner=M['inner'], params=M['params'], iters=M['iters'], n_feat=len(cols), bins=rows)
for k, v in R.items(): print(k, v if not isinstance(v, float) else round(v, 4), flush=True)
pickle.dump(dict(res=R, M=M, ref=ref, qf=qf), open(W + 'b_out.pkl', 'wb'))
print('통과' if (C1 and C2 and C3) else '실패')
