"""XGBoost · LightGBM · CatBoost 추가 비교. HGB와 같은 규칙: 학습구간 마지막 2개 연도로 격자·반복수 선택 → 전체 학습 재적합."""
import sys, time, warnings
import numpy as np, pandas as pd
from common_ml import *
from sklearn.metrics import roc_auc_score
import xgboost as xgb, lightgbm as lgb
from catboost import CatBoostClassifier
warnings.filterwarnings('ignore')
S = pd.read_pickle(W + 'analytic.pkl')
for P in (sys.argv[1:] or PANELS):
    tr, te = split(S, P)
    EX = extra_features(tr); te = add_logs(te, EX)
    vy = sorted(tr.svy_year.unique())[-2:]
    iv = tr.svy_year.isin(vy).values; it = (tr.svy_year <= min(vy) - 2).values
    res = []; preds = {}
    for fs, cols in {'common': COMMON, 'full': COMMON + EX}.items():
        X, Xt, y = tr[cols].astype(float), te[cols].astype(float), tr.y.values
        for c in cols:   # 학습 분위로 극단값 자르기 (run_models와 동일)
            if c in CATEG or X[c].nunique() <= 3: continue
            lo, hi = X[c].quantile([0.005, 0.995]); X[c] = X[c].clip(lo, hi); Xt[c] = Xt[c].clip(lo, hi)
        spw = 1.0
        cands = {
            'XGBoost': [dict(max_depth=d, min_child_weight=m, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8,
                             reg_lambda=1.0) for d in (3, 5) for m in (5, 30)],
            'LightGBM': [dict(num_leaves=n, min_child_samples=m, learning_rate=0.03, subsample=0.8, subsample_freq=1,
                              colsample_bytree=0.8, reg_lambda=1.0, verbose=-1) for n in (15, 31) for m in (40, 150)],
            'CatBoost': [dict(depth=d, l2_leaf_reg=l, learning_rate=0.05) for d in (4, 6) for l in (3, 10)],
        }
        for name, grid in cands.items():
            t0 = time.time(); best = None
            for g in grid:
                if name == 'XGBoost':
                    m = xgb.XGBClassifier(n_estimators=3000, tree_method='hist', eval_metric='auc',
                                          early_stopping_rounds=100, n_jobs=2, random_state=42, **g)
                    m.fit(X[it], y[it], eval_set=[(X[iv], y[iv])], verbose=False); n = m.best_iteration + 1
                    a = roc_auc_score(y[iv], m.predict_proba(X[iv])[:, 1])
                elif name == 'LightGBM':
                    m = lgb.LGBMClassifier(n_estimators=3000, n_jobs=2, random_state=42, **g)
                    m.fit(X[it], y[it], eval_set=[(X[iv], y[iv])], eval_metric='auc',
                          callbacks=[lgb.early_stopping(100, verbose=False)]); n = m.best_iteration_
                    a = roc_auc_score(y[iv], m.predict_proba(X[iv])[:, 1])
                else:
                    m = CatBoostClassifier(iterations=3000, eval_metric='AUC', od_type='Iter', od_wait=100,
                                           random_seed=42, verbose=False, thread_count=2, **g)
                    m.fit(X[it], y[it], eval_set=(X[iv], y[iv]), use_best_model=True); n = m.get_best_iteration() + 1
                    a = roc_auc_score(y[iv], m.predict_proba(X[iv])[:, 1])
                if best is None or a > best[0]: best = (a, g, n)
            a_in, g, n = best; n = max(50, int(n * 1.1))
            if name == 'XGBoost': m = xgb.XGBClassifier(n_estimators=n, tree_method='hist', n_jobs=2, random_state=42, **g)
            elif name == 'LightGBM': m = lgb.LGBMClassifier(n_estimators=n, n_jobs=2, random_state=42, **g)
            else: m = CatBoostClassifier(iterations=n, random_seed=42, verbose=False, thread_count=2, **g)
            m.fit(X, y); s = m.predict_proba(Xt)[:, 1]; auc = roc_auc_score(te.y, s)
            preds[f'{fs}|{name}'] = s
            res.append(dict(panel=P, fs=fs, model=name, auc=auc, sec=round(time.time() - t0, 1), inner=a_in,
                            params=str(g), iters=n))
            print(P, fs, name, round(auc, 4), 'inner', round(a_in, 4), round(time.time() - t0), 's', flush=True)
    pd.DataFrame(res).to_csv(W + f'res_gbm3_{P}.csv', index=False)
    pd.DataFrame(preds).to_pickle(W + f'preds_gbm3_{P}.pkl')
print('DONE gbm3')
