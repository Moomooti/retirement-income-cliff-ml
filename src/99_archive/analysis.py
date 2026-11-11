"""결과 종합: AUC 표, DeLong, 랜덤효과 메타, 순열 중요도, 보정, 사업 지표."""
import numpy as np, pandas as pd, pickle, warnings, json
from common_ml import *
from sklearn.metrics import roc_auc_score, brier_score_loss, average_precision_score
from sklearn.inspection import permutation_importance
warnings.filterwarnings('ignore')
R = pd.concat([pd.read_csv(W + f'res_{p}.csv') for p in PANELS] + [pd.read_csv(W + f'res_gbm3_{p}.csv') for p in PANELS])
R.to_csv(W + 'all_results.csv', index=False)
out = {}
# ---- 사전 등록 비교 ----
rows = []
PR = {}
for p in PANELS:
    d = pd.read_pickle(W + f'preds_{p}.pkl'); g3 = pd.read_pickle(W + f'preds_gbm3_{p}.pkl')
    for c in g3: d[c] = g3[c].values
    PR[p] = d
    y = d.y.values
    for comp, a, b in [('full_vs_B0', 'full|HGB_tuned', 'B0_income_only'),
                       ('common_vs_B0', 'common|HGB_tuned', 'B0_income_only'),
                       ('full_vs_B1', 'full|HGB_tuned', 'B1_calculator'),
                       ('full_vs_common', 'full|HGB_tuned', 'common|HGB_tuned'),
                       ('stack_vs_B0', 'full|Stacking', 'B0_income_only'),
                       ('full_vs_linear', 'full|HGB_tuned', 'full|LR_L2'),
                       ('lgbm_vs_B0', 'full|LightGBM', 'B0_income_only'), ('xgb_vs_B0', 'full|XGBoost', 'B0_income_only'),
                       ('cat_vs_B0', 'full|CatBoost', 'B0_income_only')]:
        A, B, dlt, se, pv, seA = delong_diff(y, d[a].values, d[b].values)
        rows.append(dict(panel=p, comp=comp, auc_a=A, auc_b=B, delta=dlt, se=se, p=pv, n=len(y), pos=y.sum(),
                         se_a=seA))
C = pd.DataFrame(rows); out['compare'] = C
print(C[C.comp.isin(['full_vs_B0', 'common_vs_B0'])].round(4).to_string())
MA = {}
for comp in C.comp.unique():
    c = C[C.comp == comp]; MA[comp] = meta_dl(c.delta, c.se)
# 통합 AUC (메타, 로짓 아님 - 단순 역분산)
for k, col in [('auc_full', 'full|HGB_tuned'), ('auc_b0', 'B0_income_only'), ('auc_common', 'common|HGB_tuned')]:
    e, s = [], []
    for p in PANELS:
        aucs, Sg = delong(PR[p].y.values, PR[p][col].values); e.append(aucs[0]); s.append(np.sqrt(Sg[0, 0]))
    MA[k] = meta_dl(e, s)
out['meta'] = MA
for k, v in MA.items(): print(k, {a: round(b, 4) for a, b in v.items()})
# ---- 사업 지표: 경보 예산(상위 10%/20%) ----
biz = []
for p in PANELS:
    d = PR[p]; y = d.y.values
    for col, lab in [('full|HGB_tuned', 'ML'), ('B0_income_only', '현재소득'), ('B1_calculator', '계산기')]:
        s = d[col].values
        for q in [0.1, 0.2, 0.3]:
            thr = np.quantile(s, 1 - q); f = s >= thr
            biz.append(dict(panel=p, model=lab, budget=q, precision=y[f].mean(), recall=y[f].sum() / y.sum(),
                            lift=y[f].mean() / y.mean(), base=y.mean()))
        if lab == 'ML':
            biz_ap = average_precision_score(y, s)
B = pd.DataFrame(biz); out['biz'] = B
print(B[B.budget == 0.2].pivot(index='panel', columns='model', values='recall').round(3))
# ---- 위험 10분위별 실제 하락률 (ML vs 현재소득) ----
dec = []
for p in PANELS:
    d = PR[p]
    for col, lab in [('full|HGB_tuned', 'ML'), ('B0_income_only', '현재소득')]:
        r = pd.qcut(d[col].rank(method='first'), 10, labels=False)
        g = d.groupby(r).y.mean()
        for i, v in g.items(): dec.append(dict(panel=p, model=lab, decile=i + 1, rate=v))
out['deciles'] = pd.DataFrame(dec)
# ---- 순열 중요도 + 보정 (full HGB_tuned) ----
imp, cal = [], []
for p in PANELS:
    M = pickle.load(open(W + f'meta_{p}.pkl', 'rb'))
    mm = M['meta']['full']; m, Xte = mm['model'], mm['Xte']
    y = PR[p].y.values
    pi = permutation_importance(m, Xte, y, scoring='roc_auc', n_repeats=5, random_state=0, n_jobs=1)
    for c, v, s in zip(Xte.columns, pi.importances_mean, pi.importances_std):
        imp.append(dict(panel=p, feature=c, imp=v, sd=s))
    pr = m.predict_proba(Xte)[:, 1]
    q = pd.qcut(pr, 10, labels=False, duplicates='drop')
    for i in np.unique(q):
        cal.append(dict(panel=p, bin=i, pred=pr[q == i].mean(), obs=y[q == i].mean()))
    out.setdefault('brier', {})[p] = dict(brier=brier_score_loss(y, pr), base=brier_score_loss(y, np.full(len(y), y.mean())),
                                          mean_pred=pr.mean(), obs=y.mean(), ap=average_precision_score(y, pr),
                                          ap_b0=average_precision_score(y, PR[p]['B0_income_only']))
    out.setdefault('hgb_params', {})[p] = dict(params=mm['best'][1], iters=mm['best'][2], inner_auc=mm['best'][0],
                                               n_feat=len(mm['cols']), n_tr=M['n_tr'], n_te=M['n_te'],
                                               pos_tr=M['pos_tr'], pos_te=M['pos_te'])
out['imp'] = pd.DataFrame(imp); out['cal'] = pd.DataFrame(cal)
print(out['imp'].sort_values('imp', ascending=False).groupby('panel').head(6).to_string())
print(json.dumps(out['brier'], indent=1, default=float))
pickle.dump(out, open(W + 'analysis_out.pkl', 'wb'))
print('DONE')
