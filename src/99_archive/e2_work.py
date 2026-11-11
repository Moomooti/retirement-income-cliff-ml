"""E2 일 전환 정답 봉인 시험 (prereg_E124.txt)"""
import numpy as np, pandas as pd, pickle, warnings
from common_ml import *
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import lightgbm as lgb
warnings.filterwarnings('ignore')
SA = pd.read_pickle(W + 'analytic_all.pkl')
P = pd.concat([pd.read_pickle(W + f'p_{p}.pkl') for p in ['koweps', 'klips', 'nastab', 'khp', 'klosa', 'kreis']], ignore_index=True)
key = ['panel', 'pid', 'svy_year']
E = P[key + ['employed']].drop_duplicates(key).copy(); E['svy_year'] -= 2; E = E.rename(columns={'employed': 'emp_f2'})
SA = SA.merge(E, on=key, how='left')
res, rows = [], []
for lab, pop, yfun in [('T1 그만둠', lambda d: d.employed == 1, lambda d: (d.emp_f2 == 0)),
                       ('T2 재취업', lambda d: d.employed == 0, lambda d: (d.emp_f2 == 1))]:
    D = SA[pop(SA) & SA.emp_f2.notna() & SA.age.between(50, 69)].copy(); D['y'] = yfun(D).astype(int)
    for p in PANELS:
        tr, te = split(D, p)
        if te.y.sum() < 20 or (1 - te.y).sum() < 20 or tr.y.sum() < 50:
            rows.append(dict(label=lab, panel=p, n_te=len(te), pos_te=te.y.sum(), status='인원 부족')); continue
        EX = extra_features(tr); te = add_logs(te, EX); cols = COMMON + EX
        X, Xt, y = tr[cols].astype(float), te[cols].astype(float), tr.y.values
        vy = sorted(tr.svy_year.unique())[-2:]; iv = tr.svy_year.isin(vy).values; it = (tr.svy_year <= min(vy) - 2).values
        best = None
        for g in [dict(num_leaves=n, min_child_samples=m) for n in (15, 31) for m in (40, 150)]:
            m = lgb.LGBMClassifier(n_estimators=3000, learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=42, **g)
            m.fit(X[it], y[it], eval_set=[(X[iv], y[iv])], eval_metric='auc', callbacks=[lgb.early_stopping(100, verbose=False)])
            a = roc_auc_score(y[iv], m.predict_proba(X[iv])[:, 1])
            if best is None or a > best[0]: best = (a, g, m.best_iteration_)
        L = lgb.LGBMClassifier(n_estimators=max(50, int(best[2] * 1.1)), learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=42, **best[1]).fit(X, y)
        sL = L.predict_proba(Xt)[:, 1]
        sR = make_pipeline(SimpleImputer(add_indicator=True), StandardScaler(), LogisticRegression(max_iter=3000)).fit(X, y).predict_proba(Xt)[:, 1]
        calc = make_pipeline(SimpleImputer(), StandardScaler(), LogisticRegression()).fit(tr[['age', 'log_ratio']], y)
        sC = calc.predict_proba(te[['age', 'log_ratio']])[:, 1]
        A_, B_, dl, se, pv_, _ = delong_diff(te.y.values, sL, sC)
        A2, B2, dl2, se2, pv2, _ = delong_diff(te.y.values, sL, sR)
        lo = dl - 1.96 * se
        rows.append(dict(label=lab, panel=p, n_tr=len(tr), n_te=len(te), pos_te=int(te.y.sum()), rate_te=te.y.mean(), auc_calc=B_, auc_lr=B2, auc_lgb=A_,
                         d_calc=dl, se_calc=se, lo_calc=lo, p_calc=pv_, d_lr=dl2, se_lr=se2, p_lr=pv2, status='통과' if lo > 0 else ('방향 일치' if dl > 0 else '실패')))
        print(lab, p, len(te), int(te.y.sum()), 'calc', round(B_, 3), 'LR', round(B2, 3), 'LGB', round(A_, 3), 'Δcalc', round(dl, 3), 'lo', round(lo, 3), rows[-1]['status'], flush=True)
R = pd.DataFrame(rows)
summ = {}
for lab, g in R.groupby('label'):
    gg = g[g.status != '인원 부족']; npass = int((gg.status == '통과').sum())
    summ[lab] = dict(n_calc=len(gg), n_pass=npass, verdict='성공' if npass >= 0.8 * len(gg) else '실패',
                     meta_calc=meta_dl(gg.d_calc, gg.se_calc), meta_lr=meta_dl(gg.d_lr, gg.se_lr))
    print(lab, summ[lab]['verdict'], f'{npass}/{len(gg)}', 'meta Δcalc', round(summ[lab]['meta_calc']['est'], 4), 'meta Δlr', round(summ[lab]['meta_lr']['est'], 4))
pickle.dump(dict(R=R, summ=summ), open(W + 'e2_out.pkl', 'wb'))
