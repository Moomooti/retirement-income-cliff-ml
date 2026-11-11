"""P1~P6 ML 프로세스 점검 실험 (prereg_P16.txt)"""
import numpy as np, pandas as pd, pickle, warnings, ast, time, sys, os
from common_ml import *
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.model_selection import GroupKFold
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import SimpleImputer, IterativeImputer
from sklearn.linear_model import LogisticRegression
from scipy.stats import rankdata
import lightgbm as lgb, xgboost as xgb
from catboost import CatBoostClassifier
warnings.filterwarnings('ignore')
SEL = sys.argv[1:]
O = pickle.load(open(W + 'v3_out.pkl', 'rb')); TU = pd.DataFrame(O['tune']); PRED = pickle.load(open(W + 'v3_pred.pkl', 'rb'))
TASKS = ['KOWEPS_r', 'NaSTaB_r', 'KReIS_r', 'KReIS_rn', 'KLIPS_r']; JUDGE = TASKS[:3]
lgt = lambda q: np.log(np.clip(q, 1e-6, 1 - 1e-6) / (1 - np.clip(q, 1e-6, 1 - 1e-6)))
out = {}


def load(k):
    p, base = k.split('_')
    tr, te, cols = pickle.load(open(W + f'v3_data_{p}_{base}.pkl', 'rb')); tr, te = tr.reset_index(drop=True), te.reset_index(drop=True)
    X, Xt = tr[cols].astype(float), te[cols].astype(float)
    for c in X.columns:
        if c in CATEG or X[c].nunique() <= 3: continue
        lo, hi = X[c].quantile([0.005, 0.995]); X[c] = X[c].clip(lo, hi); Xt[c] = Xt[c].clip(lo, hi)
    vy = sorted(tr.svy_year.unique())[-2:]; iv = tr.svy_year.isin(vy).values; it = (tr.svy_year <= min(vy) - 4).values
    return tr, te, cols, X, Xt, tr.y.values, te.y.values, it, iv


def prm(k, model):
    t = TU[(TU.task == k) & (TU.model == model)].iloc[0]
    return (t.params if isinstance(t.params, dict) else ast.literal_eval(t.params)), int(t.iters)


def mk_lgb(k, **kw):
    g, n = prm(k, 'LightGBM'); a = dict(n_estimators=n, learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                                        verbose=-1, n_jobs=2, random_state=42, **g); a.update(kw); return lgb.LGBMClassifier(**a)


def judge(rows, a, b):
    """rows: dict task -> (y, sa, sb). returns per-task df + meta over JUDGE"""
    R = []
    for k, (y, sa, sb) in rows.items():
        A_, B_, d, se, p, _ = delong_diff(y, sa, sb); R.append(dict(task=k, auc_a=A_, auc_b=B_, d=d, se=se, p=p))
    R = pd.DataFrame(R); J = R[R.task.isin(JUDGE)]; m = meta_dl(J.d, J.se)
    return R, m


def ece(y, q, b=10):
    e = 0; edges = np.quantile(q, np.linspace(0, 1, b + 1))
    idx = np.clip(np.searchsorted(edges, q, side='right') - 1, 0, b - 1)
    for i in range(b):
        m = idx == i
        if m.any(): e += m.mean() * abs(q[m].mean() - y[m].mean())
    return e


# ======================= P5 =======================
if 'P5' in SEL:
    rows, dca, boot = [], [], []
    for k in TASKS:
        d = PRED[k]; y = d.y.values; n = len(y)
        S = {'지금 소득': d['B0 지금 소득'].values, '계산기형': d['B1 계산기형'].values, '로지스틱': d['LR_L2'].values,
             'LightGBM': d['LightGBM'].values, '최종 모델': d['최종: LightGBM+로지스틱'].values}
        for nm, s in S.items():
            top = s >= np.quantile(s, 0.8)
            rows.append(dict(task=k, model=nm, base=y.mean(), auc=roc_auc_score(y, s), prauc=average_precision_score(y, s),
                             prec20=y[top].mean(), rec20=y[top].sum() / y.sum(), lift20=y[top].mean() / y.mean()))
        for pt in np.arange(0.05, 0.401, 0.01):
            r = dict(task=k, pt=pt, all=y.mean() - (1 - y.mean()) * pt / (1 - pt), none=0.0)
            for nm in ['계산기형', 'LightGBM']:
                a = S[nm] >= pt; r[nm] = (a & (y == 1)).sum() / n - (a & (y == 0)).sum() / n * pt / (1 - pt)
            dca.append(r)
        if k in JUDGE:
            rng = np.random.RandomState(42); pid = d.pid.values; up = np.unique(pid); grp = pd.Series(np.arange(n)).groupby(pid).apply(np.array).to_dict()
            bs = []
            for _ in range(1000):
                ii = np.concatenate([grp[u] for u in rng.choice(up, len(up))])
                if y[ii].sum() == 0: continue
                bs.append(average_precision_score(y[ii], S['최종 모델'][ii]) - average_precision_score(y[ii], S['지금 소득'][ii]))
            boot.append(dict(task=k, d=average_precision_score(y, S['최종 모델']) - average_precision_score(y, S['지금 소득']),
                             lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5)))
        print('P5', k, 'done', flush=True)
    R = pd.DataFrame(rows); D = pd.DataFrame(dca); B = pd.DataFrame(boot)
    pv = R.pivot(index='task', columns='model', values='prauc')
    okA = bool((pv['최종 모델'] > pv['지금 소득']).all() and (B.lo > 0).all())
    win = D[(D.pt >= 0.095) & (D.pt <= 0.305)].groupby('task')[['all', '계산기형', 'LightGBM']].mean()
    okB = int((win.LightGBM > win[['계산기형', 'all']].max(axis=1)).sum())
    out.update(P5=R, P5_dca=D, P5_boot=B, P5_win=win, P5_A='성공' if okA else '실패', P5_B='성공' if okB >= 4 else '실패', P5_Bok=okB)
    print(R.round(3).to_string(), '\n', B.round(4), '\n', win.round(4), out['P5_A'], out['P5_B'], okB, flush=True)

# ======================= P6 =======================
if 'P6' in SEL:
    k = 'KOWEPS_r'; tr, te, cols, X, Xt, y, yt, it, iv = load(k)
    m = mk_lgb(k).fit(X, y); bst = m.booster_; s = bst.model_to_string()
    one = Xt.iloc[[0]]; t1, t2 = [], []
    for i in range(1000):
        r = Xt.iloc[[i % len(Xt)]]
        a = time.perf_counter(); m.predict_proba(r); t1.append(time.perf_counter() - a)
        a = time.perf_counter(); m.predict_proba(r); bst.predict(r, pred_contrib=True); t2.append(time.perf_counter() - a)
    big = Xt.sample(100000, replace=True, random_state=0)
    a = time.perf_counter(); m.predict_proba(big); tb = time.perf_counter() - a
    a = time.perf_counter(); bst.predict(big, pred_contrib=True); tbs = time.perf_counter() - a
    out['P6'] = dict(ms_one=np.median(t1) * 1000, ms_one_p95=np.percentile(t1, 95) * 1000, ms_one_shap=np.median(t2) * 1000,
                     ms_one_shap_p95=np.percentile(t2, 95) * 1000, s_batch=tb, s_batch_shap=tbs, kb=len(s.encode()) / 1024,
                     trees=bst.num_trees(), n_feat=len(cols))
    out['P6_verdict'] = '실시간 + 배치 가능' if (out['P6']['ms_one_shap'] < 50 and tb < 60) else '조건 미달'
    print('P6', out['P6'], out['P6_verdict'], flush=True)

# ======================= P2 =======================
if 'P2' in SEL:
    res, rows = [], {'spw': {}, 'under': {}}
    for k in TASKS:
        tr, te, cols, X, Xt, y, yt, it, iv = load(k); base = PRED[k]['LightGBM'].values
        sp = mk_lgb(k, scale_pos_weight=(y == 0).sum() / (y == 1).sum()).fit(X, y).predict_proba(Xt)[:, 1]
        rng = np.random.RandomState(42); pos = np.where(y == 1)[0]; neg = rng.choice(np.where(y == 0)[0], len(pos), replace=False); ii = np.r_[pos, neg]
        un = mk_lgb(k).fit(X.iloc[ii], y[ii]).predict_proba(Xt)[:, 1]
        for nm, s in [('v3 (처리 없음)', base), ('가중치(scale_pos_weight)', sp), ('언더샘플링 1:1', un)]:
            top = s >= np.quantile(s, 0.8)
            res.append(dict(task=k, method=nm, auc=roc_auc_score(yt, s), rec20=yt[top].sum() / yt.sum(), brier=brier_score_loss(yt, s), ece=ece(yt, s),
                            mean_pred=s.mean(), obs=yt.mean()))
        rows['spw'][k] = (yt, sp, base); rows['under'][k] = (yt, un, base)
        print('P2', k, flush=True)
    out['P2'] = pd.DataFrame(res)
    out['P2_spw'], out['P2_spw_meta'] = judge(rows['spw'], 0, 0); out['P2_un'], out['P2_un_meta'] = judge(rows['under'], 0, 0)
    out['P2_verdict'] = '채택' if (out['P2_spw_meta']['lo'] > 0 or out['P2_un_meta']['lo'] > 0) else '불채택'
    print(out['P2'].round(3).to_string(), out['P2_spw_meta'], out['P2_un_meta'], out['P2_verdict'], flush=True)

# ======================= P4 =======================
if 'P4' in SEL:
    res, rows = [], {'med': {}, 'iter': {}}
    for k in TASKS:
        tr, te, cols, X, Xt, y, yt, it, iv = load(k); base = PRED[k]['LightGBM'].values
        miss = X.isna().mean(); mc = miss[miss > 0].index.tolist()
        ind = lambda Z: Z[mc].isna().astype(float).add_suffix('_na')
        sm = SimpleImputer(strategy='median').fit(X); Xm = pd.DataFrame(sm.transform(X), columns=cols).join(ind(X)); Xtm = pd.DataFrame(sm.transform(Xt), columns=cols).join(ind(Xt))
        a = time.time()
        ii_ = IterativeImputer(max_iter=5, random_state=42, sample_posterior=False).fit(X)
        Xi = pd.DataFrame(ii_.transform(X), columns=cols).join(ind(X)); Xti = pd.DataFrame(ii_.transform(Xt), columns=cols).join(ind(Xt))
        s_m = mk_lgb(k).fit(Xm, y).predict_proba(Xtm)[:, 1]; s_i = mk_lgb(k).fit(Xi, y).predict_proba(Xti)[:, 1]
        for nm, s in [('LightGBM 기본 처리 (v3)', base), ('중앙값 + 결측 표시', s_m), ('반복 대체 + 결측 표시', s_i)]:
            res.append(dict(task=k, method=nm, auc=roc_auc_score(yt, s)))
        res.append(dict(task=k, method='_info', miss_cols=len(mc), miss_mean=miss.mean(), miss_max=miss.max(), miss_rows=X.isna().any(axis=1).mean()))
        rows['med'][k] = (yt, s_m, base); rows['iter'][k] = (yt, s_i, base)
        print('P4', k, round(time.time() - a), flush=True)
    out['P4'] = pd.DataFrame(res)
    out['P4_med'], out['P4_med_meta'] = judge(rows['med'], 0, 0); out['P4_it'], out['P4_it_meta'] = judge(rows['iter'], 0, 0)
    out['P4_verdict'] = '교체' if (out['P4_med_meta']['lo'] > 0 or out['P4_it_meta']['lo'] > 0) else 'v3 유지'
    print(out['P4'].round(4).to_string(), out['P4_med_meta'], out['P4_it_meta'], out['P4_verdict'], flush=True)

# ======================= P3 =======================
if 'P3' in SEL:
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    res, rows, coefs = [], {}, []
    for k in TASKS:
        tr, te, cols, X, Xt, y, yt, it, iv = load(k); t0 = time.time()
        gx, nx = prm(k, 'XGBoost'); gc, nc = prm(k, 'CatBoost')
        makers = {'LightGBM': lambda: mk_lgb(k),
                  'XGBoost': lambda: xgb.XGBClassifier(n_estimators=nx, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, tree_method='hist', n_jobs=2, random_state=42, **gx),
                  'CatBoost': lambda: CatBoostClassifier(iterations=nc, learning_rate=0.05, random_seed=42, verbose=False, thread_count=2, **gc),
                  'LR_L2': lambda: make_pipeline(SimpleImputer(strategy='median', add_indicator=True), StandardScaler(), LogisticRegression(C=1.0, max_iter=3000))}
        oof = np.zeros((len(y), 4))
        for a_, b_ in GroupKFold(5).split(X, y, tr.pid.values):
            for j, (nm, f) in enumerate(makers.items()):
                oof[b_, j] = f().fit(X.iloc[a_], y[a_]).predict_proba(X.iloc[b_])[:, 1]
        meta = LogisticRegression(C=1.0, max_iter=1000).fit(lgt(oof), y)
        T = np.column_stack([PRED[k][nm].values for nm in makers]); st = meta.predict_proba(lgt(T))[:, 1]
        fin = PRED[k]['최종: LightGBM+로지스틱'].values
        res.append(dict(task=k, auc_stack=roc_auc_score(yt, st), auc_final=roc_auc_score(yt, fin), auc_lgb=roc_auc_score(yt, PRED[k]['LightGBM']),
                        oof_aucs={nm: roc_auc_score(y, oof[:, j]) for j, nm in enumerate(makers)}))
        coefs.append(dict(task=k, **{nm: c for nm, c in zip(makers, meta.coef_[0])}))
        rows[k] = (yt, st, fin); print('P3', k, round(time.time() - t0), res[-1], coefs[-1], flush=True)
    out['P3'] = pd.DataFrame(res); out['P3_coef'] = pd.DataFrame(coefs)
    out['P3_d'], out['P3_meta'] = judge(rows, 0, 0)
    out['P3_verdict'] = '채택' if out['P3_meta']['lo'] > 0 else '순위 평균 유지'
    print(out['P3_d'].round(4), out['P3_meta'], out['P3_verdict'], flush=True)

# ======================= P1 =======================
if 'P1' in SEL:
    import optuna; optuna.logging.set_verbosity(optuna.logging.WARNING)
    res, rows, best = [], {}, []
    for k in TASKS:
        tr, te, cols, X, Xt, y, yt, it, iv = load(k); t0 = time.time()
        def obj(tr_):
            g = dict(num_leaves=tr_.suggest_int('num_leaves', 7, 127, log=True), min_child_samples=tr_.suggest_int('min_child_samples', 10, 400, log=True),
                     learning_rate=tr_.suggest_float('learning_rate', 0.01, 0.1, log=True), colsample_bytree=tr_.suggest_float('feature_fraction', 0.4, 1.0),
                     subsample=tr_.suggest_float('bagging_fraction', 0.5, 1.0), reg_alpha=tr_.suggest_float('lambda_l1', 1e-3, 10, log=True),
                     reg_lambda=tr_.suggest_float('lambda_l2', 1e-3, 10, log=True), min_split_gain=tr_.suggest_float('min_split_gain', 0, 1))
            m = lgb.LGBMClassifier(n_estimators=3000, subsample_freq=1, verbose=-1, n_jobs=2, random_state=42, **g)
            m.fit(X[it], y[it], eval_set=[(X[iv], y[iv])], eval_metric='auc', callbacks=[lgb.early_stopping(100, verbose=False)])
            tr_.set_user_attr('n', m.best_iteration_ or 3000); tr_.set_user_attr('g', g)
            return roc_auc_score(y[iv], m.predict_proba(X[iv], num_iteration=m.best_iteration_)[:, 1])
        st = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=42)); st.optimize(obj, n_trials=60)
        g = st.best_trial.user_attrs['g']; n = max(50, int(st.best_trial.user_attrs['n'] * 1.1))
        s_t = lgb.LGBMClassifier(n_estimators=n, subsample_freq=1, verbose=-1, n_jobs=2, random_state=42, **g).fit(X, y).predict_proba(Xt)[:, 1]
        base = PRED[k]['LightGBM'].values; old_inner = TU[(TU.task == k) & (TU.model == 'LightGBM')].inner.iloc[0]
        fin_t = rankdata(s_t) + rankdata(PRED[k]['LR_L2'].values)
        res.append(dict(task=k, inner_old=old_inner, inner_new=st.best_value, auc_old=roc_auc_score(yt, base), auc_new=roc_auc_score(yt, s_t),
                        auc_fin_old=roc_auc_score(yt, PRED[k]['최종: LightGBM+로지스틱']), auc_fin_new=roc_auc_score(yt, fin_t), iters=n,
                        trials_auc=[t.value for t in st.trials]))
        best.append(dict(task=k, **{a: (round(b, 4) if isinstance(b, float) else b) for a, b in g.items()}))
        rows[k] = (yt, s_t, base); print('P1', k, round(time.time() - t0), {a: b for a, b in res[-1].items() if a != 'trials_auc'}, flush=True)
    out['P1'] = pd.DataFrame(res); out['P1_best'] = pd.DataFrame(best)
    out['P1_d'], out['P1_meta'] = judge(rows, 0, 0)
    out['P1_verdict'] = '튜닝 이득' if out['P1_meta']['lo'] > 0 else '튜닝 부족 아님'
    print(out['P1_d'].round(4), out['P1_meta'], out['P1_verdict'], flush=True)
pickle.dump(out, open(W + f'p16_out_{"".join(SEL)}.pkl', 'wb'))
