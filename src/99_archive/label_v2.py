"""정답 재설계 실험 (노트 반영): 4년 관측 기반 지속형/반복형 정답. 시험셋은 4년 뒤가 관측되는 최근 2개 기준 차수로 새로 봉인."""
import numpy as np, pandas as pd, pickle, warnings, sys
from common_ml import *
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import lightgbm as lgb
warnings.filterwarnings('ignore')
SA = pd.read_pickle(W + 'analytic_all.pkl')
SA = SA[SA.ratio_f4.notna()].copy()
LABELS = {
    'L1_지속하락': (lambda d: d.ratio >= 1, lambda d: (d.ratio_f2 < 1) & (d.ratio_f4 < 1)),
    'L2_반복부족_전체': (lambda d: d.ratio > 0, lambda d: (d.ratio_f2 < 1) & (d.ratio_f4 < 1)),
    'L3_4년평균하락': (lambda d: d.ratio >= 1, lambda d: np.sqrt(d.ratio_f2 * d.ratio_f4) < 1),
}
sel = sys.argv[1:] or list(LABELS)
res, preds = [], {}
for ln in sel:
    pop, lab = LABELS[ln]
    D = SA[pop(SA)].copy(); D['y'] = lab(D).astype(int)
    for p in PANELS:
        d = D[D.panel == p]
        ys = sorted(d.svy_year.unique()); ty = ys[-2:]
        te = d[d.svy_year.isin(ty)].copy(); tr = d[d.svy_year <= min(ty) - 4].copy()
        EX = extra_features(tr); te = add_logs(te, EX); cols = COMMON + EX
        X, Xt, y = tr[cols].astype(float), te[cols].astype(float), tr.y.values
        vy = sorted(tr.svy_year.unique())[-2:]; iv = tr.svy_year.isin(vy).values; it = (tr.svy_year <= min(vy) - 4).values
        best = None
        for g in [dict(num_leaves=n, min_child_samples=m) for n in (15, 31) for m in (40, 150)]:
            m = lgb.LGBMClassifier(n_estimators=3000, learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                                   reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=42, **g)
            m.fit(X[it], y[it], eval_set=[(X[iv], y[iv])], eval_metric='auc', callbacks=[lgb.early_stopping(100, verbose=False)])
            a = roc_auc_score(y[iv], m.predict_proba(X[iv])[:, 1])
            if best is None or a > best[0]: best = (a, g, m.best_iteration_)
        m = lgb.LGBMClassifier(n_estimators=max(50, int(best[2] * 1.1)), learning_rate=0.03, subsample=0.8, subsample_freq=1,
                               colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=42, **best[1]).fit(X, y)
        s_ml = m.predict_proba(Xt)[:, 1]
        lr = make_pipeline(SimpleImputer(add_indicator=True), StandardScaler(), LogisticRegression(max_iter=3000)).fit(X.fillna(np.nan), y)
        s_lr = lr.predict_proba(Xt)[:, 1]
        s_b0 = -te.log_ratio.values
        A, B, dl, se, pv_, _ = delong_diff(te.y.values, s_ml, s_b0)
        res.append(dict(label=ln, panel=p, n_tr=len(tr), n_te=len(te), te_years=f'{ty[0]}·{ty[1]}', pos_te=te.y.mean(),
                        auc_b0=B, auc_lr=roc_auc_score(te.y, s_lr), auc_ml=A, delta=dl, se=se, p=pv_, inner=best[0]))
        preds[(ln, p)] = pd.DataFrame(dict(y=te.y.values, pid=te.pid.values, svy_year=te.svy_year.values, ml=s_ml, lr=s_lr, b0=s_b0,
                                           ratio=te.ratio.values))
        print(ln, p, len(tr), len(te), round(te.y.mean(), 3), 'B0', round(B, 3), 'LR', round(res[-1]['auc_lr'], 3), 'ML', round(A, 3), flush=True)
R = pd.DataFrame(res)
for ln, g in R.groupby('label'):
    m = meta_dl(g.delta, g.se); print(ln, 'mean ML', round(g.auc_ml.mean(), 3), 'B0', round(g.auc_b0.mean(), 3), 'meta d', round(m['est'], 4), [round(m['lo'], 4), round(m['hi'], 4)])
R.to_csv(W + 'label_v2.csv', index=False); pickle.dump(preds, open(W + 'label_v2_preds.pkl', 'wb'))
