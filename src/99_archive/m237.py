"""M2 사각지대 · M3 닮은 사람 · M7 가장 작은 변화 (prereg_M237.txt)"""
import numpy as np, pandas as pd, pickle, warnings, ast, itertools, sys
from scipy.stats import spearmanr
from common_ml import *
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.inspection import permutation_importance
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import lightgbm as lgb
warnings.filterwarnings('ignore')
SEL = sys.argv[1:] or ['M2', 'M3', 'M7']
O = pickle.load(open(W + 'v3_out.pkl', 'rb')); TU = pd.DataFrame(O['tune']); PRED = pickle.load(open(W + 'v3_pred.pkl', 'rb'))
out = {}


def load(p, base='r'):
    tr, te, cols = pickle.load(open(W + f'v3_data_{p}_{base}.pkl', 'rb')); tr, te = tr.reset_index(drop=True), te.reset_index(drop=True)
    X, Xt = tr[cols].astype(float), te[cols].astype(float)
    for c in X.columns:
        if c in CATEG or X[c].nunique() <= 3: continue
        lo, hi = X[c].quantile([0.005, 0.995]); X[c] = X[c].clip(lo, hi); Xt[c] = Xt[c].clip(lo, hi)
    k = f'{p}_{base}'; t = TU[(TU.task == k) & (TU.model == 'LightGBM')].iloc[0]
    prm = t.params if isinstance(t.params, dict) else ast.literal_eval(t.params)
    mk = lambda n=int(t.iters): lgb.LGBMClassifier(n_estimators=n, learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                                                    reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=42, **prm)
    vy = sorted(tr.svy_year.unique())[-2:]; iv = tr.svy_year.isin(vy).values; it = (tr.svy_year <= min(vy) - 4).values
    return tr, te, cols, X, Xt, mk, it, iv


# ======================= M2 =======================
if 'M2' in SEL:
    D = '/home/claude/raw/2_KLIPS_1-27_stata/1-27#Ucc28 release  (Stata)/'
    rec = []
    for w in range(1, 18):
        ww = f'{w:02d}'; h = pd.read_stata(f'/home/claude/raw/4_NaSTaB_household_stata/NaSTaB{ww}H.dta', columns=[f'hid{ww}', f'h{ww}ea001'], convert_categoricals=False).dropna(subset=[f'hid{ww}'])
        rec.append(pd.DataFrame(dict(panel='NaSTaB', hid=h[f'hid{ww}'].astype('int64').astype(str), svy_year=2007 + w, recv=(h[f'h{ww}ea001'] == 1).astype(float))))
    for w in range(8, 28):
        ww = f'{w:02d}'; h = pd.read_stata(D + f'klips{ww}h.dta', columns=[f'hhid{ww}', f'h{ww}2152'], convert_categoricals=False).dropna(subset=[f'hhid{ww}'])
        rec.append(pd.DataFrame(dict(panel='KLIPS', hid=h[f'hhid{ww}'].astype('int64').astype(str), svy_year=1997 + w, recv=(h[f'h{ww}2152'].fillna(0) > 0).astype(float))))
    REC = pd.concat(rec).drop_duplicates(['panel', 'hid', 'svy_year'])
    P = pd.concat([pd.read_pickle(W + f'p_{p}.pkl') for p in ['nastab', 'klips']])[['panel', 'pid', 'hid', 'svy_year']]
    PR = P.merge(REC, on=['panel', 'hid', 'svy_year'], how='left')[['panel', 'pid', 'svy_year', 'recv']].drop_duplicates(['panel', 'pid', 'svy_year'])
    res = []
    for p in ['NaSTaB', 'KLIPS']:
        tr, te, cols, X, Xt, mk, it, iv = load(p)
        for df in (tr, te):
            anyrec = np.zeros(len(df))
            for k in [2, 3, 4]:
                f = PR.copy(); f['svy_year'] -= k
                m = df[['panel', 'pid', 'svy_year']].merge(f, on=['panel', 'pid', 'svy_year'], how='left').recv.fillna(0).values
                anyrec = np.maximum(anyrec, m)
            df['norecv'] = 1 - anyrec; df['y2'] = (df.y == 1) & (df.norecv == 1)
        y2, yt2 = tr.y2.values.astype(int), te.y2.values.astype(int); y = tr.y.values
        # ② v3 점수
        s_v3 = PRED[f'{p}_r']['LightGBM'].values
        # ③ 2단계: P(하락) × P(미수급 | 하락)
        def two_stage(Xa, ya, ya_nr, Xb):
            m1 = mk().fit(Xa, ya); sub = ya == 1
            m2 = make_pipeline(SimpleImputer(add_indicator=True), StandardScaler(), LogisticRegression(max_iter=3000)).fit(Xa[sub], ya_nr[sub])
            return m1.predict_proba(Xb)[:, 1] * m2.predict_proba(Xb)[:, 1]
        nr = tr.norecv.values.astype(int)
        in_two = roc_auc_score(y2[iv], two_stage(X[it], y[it], nr[it], X[iv]))
        in_dir = roc_auc_score(y2[iv], mk().fit(X[it], y2[it]).predict_proba(X[iv])[:, 1])
        s_two = two_stage(X, y, nr, Xt); s_dir = mk().fit(X, y2).predict_proba(Xt)[:, 1]
        chosen = '2단계' if in_two >= in_dir else '직접 학습'; s_ch = s_two if chosen == '2단계' else s_dir
        A_, B_, dl, se, pv_, _ = delong_diff(yt2, s_ch, s_v3)
        r = dict(panel=p, n_te=len(te), pos=int(yt2.sum()), rate=yt2.mean(), share_norecv_among_fall=te.norecv[te.y == 1].mean(),
                 auc_b0=roc_auc_score(yt2, -te.log_dratio), auc_v3=B_, auc_two=roc_auc_score(yt2, s_two), auc_dir=roc_auc_score(yt2, s_dir),
                 inner_two=in_two, inner_dir=in_dir, chosen=chosen, auc_chosen=A_, d=dl, se=se, lo=dl - 1.96 * se, p=pv_)
        res.append(r); print('M2', r, flush=True)
    R2 = pd.DataFrame(res); out['M2'] = R2; out['M2_verdict'] = '별도 모듈 필요' if (R2.lo > 0).all() else '지속 하락 모델로 충분'
    print('M2 판정', out['M2_verdict'])

TASKS = ['KOWEPS', 'NaSTaB', 'KReIS', 'KLIPS']
# ======================= M3 =======================
if 'M3' in SEL:
    res = []
    for p in TASKS:
        tr, te, cols, X, Xt, mk, it, iv = load(p)
        m = mk().fit(X[it], tr.y.values[it])
        pi = permutation_importance(m, X[iv], tr.y.values[iv], scoring='roc_auc', n_repeats=3, random_state=0)
        wgt = np.clip(pi.importances_mean, 0, None); wgt = wgt / wgt.sum() if wgt.sum() > 0 else np.ones(len(cols)) / len(cols)
        pre = make_pipeline(SimpleImputer(strategy='median'), StandardScaler()).fit(X)
        Z, Zt = pre.transform(X) * wgt, pre.transform(Xt) * wgt
        nn = NearestNeighbors(n_neighbors=30, metric='manhattan').fit(Z)
        _, idx = nn.kneighbors(Zt); rate = tr.y.values[idx].mean(axis=1)
        yt = te.y.values; s_lgb = PRED[f'{p}_r']['LightGBM'].values
        res.append(dict(panel=p, n_te=len(te), auc_knn=roc_auc_score(yt, rate), auc_b0=roc_auc_score(yt, -te.log_dratio), auc_lgb=roc_auc_score(yt, s_lgb),
                        rho=spearmanr(rate, s_lgb).correlation, mean_rate=rate.mean(), obs=yt.mean(),
                        top_feats=[cols[i] for i in np.argsort(-wgt)[:5]]))
        print('M3', res[-1], flush=True)
    R3 = pd.DataFrame(res); ok = ((R3.auc_knn >= R3.auc_b0 + 0.02) & (R3.rho >= 0.6)).sum()
    out['M3'] = R3; out['M3_ok'] = int(ok); out['M3_verdict'] = '성공' if ok >= 3 else '실패'; print('M3 판정', out['M3_verdict'], ok)

# ======================= M7 =======================
if 'M7' in SEL:
    P_all = pd.concat([pd.read_pickle(W + f'p_{p}.pkl') for p in ['koweps', 'nastab', 'kreis', 'klips']])
    E = P_all[['panel', 'pid', 'svy_year', 'employed']].drop_duplicates(['panel', 'pid', 'svy_year']).copy(); E['svy_year'] -= 2
    E = E.rename(columns={'employed': 'emp_f2'})
    res, combos_all, direc = [], [], []
    for p in TASKS:
        tr, te, cols, X, Xt, mk, it, iv = load(p); y = tr.y.values
        L = mk().fit(X, y); s_te = L.predict_proba(Xt)[:, 1]
        oof = np.zeros(len(tr))
        for a_, b_ in GroupKFold(5).split(X, y, tr.pid): oof[b_] = mk().fit(X.iloc[a_], y[a_]).predict_proba(X.iloc[b_])[:, 1]
        thr = np.quantile(oof, 0.8); hi = s_te >= thr
        A0 = Xt[hi].copy(); raw = te[hi].reset_index(drop=True); A0 = A0.reset_index(drop=True)
        acts = []
        if 'employed' in cols: acts.append(('취업', lambda A, R: (A.assign(employed=1, **({'lost_job_2y': 0.0} if 'lost_job_2y' in A else {}))), lambda A: A.employed == 0))
        if 'x_pension_enrolled' in cols: acts.append(('공적연금 가입', lambda A, R: A.assign(x_pension_enrolled=1.0), lambda A: A.x_pension_enrolled == 0))
        if 'x_private_pension' in cols: acts.append(('개인연금 가입', lambda A, R: A.assign(x_private_pension=1.0), lambda A: A.x_private_pension == 0))
        if 'x_fin_assets' in raw:
            for amt in (1000, 3000):
                def fa(A, R, amt=amt):
                    B = A.copy(); fin = R.x_fin_assets.fillna(0).values + amt
                    if 'lg_x_fin_assets' in B: B['lg_x_fin_assets'] = np.log1p(fin)
                    if 'x_fin_assets_r' in B: B['x_fin_assets_r'] = np.clip(fin / R.hhinc.values, -50, 200)
                    return B
                acts.append((f'금융자산 +{amt:,}만원', fa, lambda A: pd.Series(True, index=A.index)))
        best = pd.Series([None] * len(A0)); done = np.zeros(len(A0), bool)
        sets = [(a,) for a in acts] + [c for c in itertools.combinations(acts, 2) if not (c[0][0].startswith('금융') and c[1][0].startswith('금융'))]
        for st in sets:
            elig = np.ones(len(A0), bool)
            B = A0.copy()
            for nm, f, cond in st: elig &= cond(A0).values; B = f(B, raw)
            sc = L.predict_proba(B[cols])[:, 1]
            hit = elig & (sc < thr) & ~done
            best[hit] = ' + '.join(nm for nm, _, _ in st); done |= hit
        n1 = best.dropna().map(lambda s: '+' not in s.replace('+1,000', '').replace('+3,000', '')).sum()
        res.append(dict(panel=p, n_high=int(hi.sum()), share_any=done.mean(), share_one=n1 / len(A0), actions=[a[0] for a in acts]))
        for c, v in best.dropna().value_counts().head(5).items(): combos_all.append(dict(panel=p, change=c, share=v / len(A0)))
        # 모델이 말하는 취업 효과(미취업자 전체, 시험셋)
        ne = Xt.employed == 0
        model_delta = (L.predict_proba(Xt[ne].assign(employed=1, **({'lost_job_2y': 0.0} if 'lost_job_2y' in Xt else {})))[:, 1] - s_te[ne.values]).mean()
        # 방향 검증 데이터: t 시점 미취업자, 점수 = 학습 OOF / 시험 예측
        allr = pd.concat([tr.assign(score=oof), te.assign(score=s_te)])
        allr = allr.merge(E, on=['panel', 'pid', 'svy_year'], how='left')
        g = allr[(allr.employed == 0) & allr.emp_f2.notna()].copy(); g['reemp'] = (g.emp_f2 == 1).astype(int)
        g['dec'] = pd.qcut(g.score.rank(method='first'), 10, labels=False); g['task'] = p
        direc.append(g[['task', 'pid', 'dec', 'reemp', 'y']])
        res[-1]['model_delta_emp'] = model_delta
        print('M7', res[-1], flush=True)
    DG = pd.concat(direc)
    def wdiff(df):
        num = den = 0
        for (_, _), q in df.groupby(['task', 'dec']):
            a, b = q[q.reemp == 1], q[q.reemp == 0]
            if len(a) >= 5 and len(b) >= 5: num += len(q) * (a.y.mean() - b.y.mean()); den += len(q)
        return num / den if den else np.nan
    est = wdiff(DG); rng = np.random.RandomState(42); keys = DG.task + '|' + DG.pid; uk = keys.unique(); idx = pd.Series(np.arange(len(DG))).groupby(keys.values).indices
    bs = [wdiff(DG.iloc[np.concatenate([idx[k] for k in rng.choice(uk, len(uk))])]) for _ in range(1000)]
    lo, hi_ = np.nanpercentile(bs, [2.5, 97.5])
    per = {t: wdiff(DG[DG.task == t]) for t in TASKS}
    R7 = pd.DataFrame(res); out['M7'] = R7; out['M7_combos'] = pd.DataFrame(combos_all)
    out['M7_dir'] = dict(est=est, lo=lo, hi=hi_, per=per, n=len(DG), reemp_rate=DG.reemp.mean())
    out['M7_verdict'] = '방향 일치 확인' if (est < 0 and hi_ < 0) else '방향 불일치'
    print('M7 방향', out['M7_dir'], out['M7_verdict'])
pickle.dump(out, open(W + f'm237_out_{"".join(SEL)}.pkl', 'wb'))
