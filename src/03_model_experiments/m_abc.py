"""M-A 개인별 설명 · M-B 적응형 질문 · M-C 판단 보류 예측 (prereg_MABC.txt)"""
import numpy as np, pandas as pd, pickle, warnings, ast, time, sys
from scipy.stats import wilcoxon
from common_ml import *
from sklearn.metrics import roc_auc_score
from sklearn.inspection import permutation_importance
import lightgbm as lgb
warnings.filterwarnings('ignore')
O = pickle.load(open(W + 'v3_out.pkl', 'rb')); TU = pd.DataFrame(O['tune'])
TASKS = [('KOWEPS', 'r'), ('NaSTaB', 'r'), ('KReIS', 'r'), ('KReIS', 'rn'), ('KLIPS', 'r')]
SEL = sys.argv[1:] or ['A', 'B', 'C']
lgt = lambda q: np.log(np.clip(q, 1e-6, 1 - 1e-6) / (1 - np.clip(q, 1e-6, 1 - 1e-6)))
out = {'A': [], 'A_top': [], 'B': [], 'C': []}
for p, base in TASKS:
    k = f'{p}_{base}'; t0 = time.time()
    tr, te, cols = pickle.load(open(W + f'v3_data_{p}_{base}.pkl', 'rb')); tr, te = tr.reset_index(drop=True), te.reset_index(drop=True)
    X, Xt = tr[cols].astype(float), te[cols].astype(float)
    for c in X.columns:
        if c in CATEG or X[c].nunique() <= 3: continue
        lo, hi = X[c].quantile([0.005, 0.995]); X[c] = X[c].clip(lo, hi); Xt[c] = Xt[c].clip(lo, hi)
    y, yt = tr.y.values, te.y.values
    t = TU[(TU.task == k) & (TU.model == 'LightGBM')].iloc[0]; prm = t.params if isinstance(t.params, dict) else ast.literal_eval(t.params)
    mk = lambda n=int(t.iters): lgb.LGBMClassifier(n_estimators=n, learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=42, **prm)
    b0 = 'log_rneed' if base == 'rn' else 'log_dratio'
    vy = sorted(tr.svy_year.unique())[-2:]; iv = tr.svy_year.isin(vy).values; it = (tr.svy_year <= min(vy) - 4).values
    # ================= M-A =================
    if 'A' in SEL:
        m = mk().fit(X, y)
        con = m.predict(Xt, pred_contrib=True)[:, :-1]          # 변수별 기여(로그 오즈), 마지막 열은 기준값
        base_lo = m.predict(Xt, raw_score=True); med = X.median()
        rng = np.random.RandomState(42); n = len(Xt); d = len(cols)
        top3 = np.argsort(-con, axis=1)[:, :3]                   # 위험을 올린 기여 상위 3
        def replaced(idx):
            Z = Xt.values.copy()
            for j in range(3): Z[np.arange(n), idx[:, j]] = med.values[idx[:, j]]
            return m.predict(pd.DataFrame(Z, columns=cols), raw_score=True)
        ch_top = np.abs(replaced(top3) - base_lo)
        ch_rnd = np.mean([np.abs(replaced(np.array([rng.choice(d, 3, replace=False) for _ in range(n)])) - base_lo) for _ in range(5)], axis=0)
        stat = wilcoxon(ch_top, ch_rnd, alternative='greater')
        auc_top = roc_auc_score(yt, replaced(top3)); auc_full = roc_auc_score(yt, base_lo)
        out['A'].append(dict(task=k, n=n, ch_top=ch_top.mean(), ch_rnd=ch_rnd.mean(), ratio=ch_top.mean() / ch_rnd.mean(), p=stat.pvalue,
                             auc_full=auc_full, auc_after_top3=auc_top))
        hi_ = base_lo >= np.quantile(base_lo, 0.8)
        first = pd.Series([cols[j] for j in top3[hi_, 0]]).value_counts(normalize=True).head(6)
        for f_, v in first.items(): out['A_top'].append(dict(task=k, feature=f_, share=v))
        # 기여도 방향 일관성: 같은 변수의 값이 클수록 기여가 커지는지(상관)
        print(k, 'M-A ratio', round(ch_top.mean() / ch_rnd.mean(), 2), 'p', stat.pvalue, flush=True)
    # ================= M-B =================
    if 'B' in SEL:
        rng = np.random.RandomState(42); d = len(cols); j0 = cols.index(b0)
        reps = []
        for r_ in range(3):
            Z = X.values.copy(); keep = rng.rand(*Z.shape) < rng.uniform(0.05, 1.0, size=(len(Z), 1)); keep[:, j0] = True
            Z[~keep] = np.nan; reps.append(Z)
        Xa = pd.DataFrame(np.vstack(reps + [X.values]), columns=cols); ya = np.concatenate([y] * 4)
        mb = mk(int(t.iters * 1.5)).fit(Xa, ya)
        # 고정 순서: 학습구간 내부 검증의 순열 중요도(같은 마스크 모델 구조로 앞부분 학습)
        Xa_it = pd.DataFrame(np.vstack([r[np.concatenate([it] * 1)] for r in reps] + [X.values[it]]), columns=cols)
        m_it = mk(int(t.iters * 1.5)).fit(Xa_it, np.concatenate([y[it]] * 4))
        pi = permutation_importance(m_it, X[iv], y[iv], scoring='roc_auc', n_repeats=3, random_state=0)
        order = [j0] + [cols.index(c) for c in pd.Series(pi.importances_mean, index=cols).sort_values(ascending=False).index if c != b0]
        sidx = np.random.RandomState(42).choice(len(Xt), min(1500, len(Xt)), replace=False)
        T = Xt.values[sidx]; ys = yt[sidx]; ns = len(T)
        prob = lambda A: mb.predict_proba(pd.DataFrame(A, columns=cols))[:, 1]
        # 고정 12 / 전체
        F12 = np.full_like(T, np.nan); F12[:, order[:12]] = T[:, order[:12]]
        auc12 = roc_auc_score(ys, prob(F12)); aucall = roc_auc_score(ys, prob(T))
        # 적응형
        A = np.full_like(T, np.nan); A[:, j0] = T[:, j0]; asked = np.zeros((ns, d), bool); asked[:, j0] = True
        active = np.ones(ns, bool); nq = np.ones(ns)
        pool = X.values; K = 10
        for step in range(19):
            idx = np.where(active)[0]
            if len(idx) == 0: break
            cand = [j for j in range(d)]
            vals = {j: pool[rng.choice(len(pool), K), j] for j in cand}
            best_v = np.full(len(idx), -1.0); best_j = np.full(len(idx), -1)
            for j in cand:
                need = ~asked[idx, j]
                if not need.any(): continue
                ii = idx[need]; B = np.repeat(A[ii], K, axis=0); B[:, j] = np.tile(vals[j], len(ii))
                v = prob(B).reshape(len(ii), K).std(axis=1)
                upd = v > best_v[need]; tmp_v = best_v[need]; tmp_j = best_j[need]; tmp_v[upd] = v[upd]; tmp_j[upd] = j
                best_v[need] = tmp_v; best_j[need] = tmp_j
            stop = (best_v < 0.01) | (best_j < 0)
            go = idx[~stop]; jj = best_j[~stop]
            A[go, jj] = T[go, jj]; asked[go, jj] = True; nq[go] += 1
            active[idx[stop]] = False
        auca = roc_auc_score(ys, prob(A))
        out['B'].append(dict(task=k, n=ns, auc_adaptive=auca, q_mean=nq.mean(), q_median=np.median(nq), q_p90=np.percentile(nq, 90),
                             auc_fixed12=auc12, auc_all=aucall, auc_b0=roc_auc_score(ys, -T[:, j0]), n_feat=d))
        print(k, 'M-B adaptive', round(auca, 3), 'q', round(nq.mean(), 1), 'fixed12', round(auc12, 3), 'all', round(aucall, 3), flush=True)
    # ================= M-C =================
    if 'C' in SEL:
        mc = mk().fit(X[it], y[it]); s_cal = mc.predict_proba(X[iv])[:, 1]; ycal = y[iv]; s_te = mc.predict_proba(Xt)[:, 1]
        a = 0.10
        # 클래스별 비적합 점수: 하락자 1 − s, 비하락자 s
        q1 = np.quantile(1 - s_cal[ycal == 1], np.ceil((1 - a) * ((ycal == 1).sum() + 1)) / (ycal == 1).sum(), method='higher')
        q0 = np.quantile(s_cal[ycal == 0], np.ceil((1 - a) * ((ycal == 0).sum() + 1)) / (ycal == 0).sum(), method='higher')
        inc1 = (1 - s_te) <= q1; inc0 = s_te <= q0
        risk_only = inc1 & ~inc0; safe_only = inc0 & ~inc1; both = inc1 & inc0; empty = ~inc1 & ~inc0
        out['C'].append(dict(task=k, n=len(yt), cov_pos=inc1[yt == 1].mean(), cov_neg=inc0[yt == 0].mean(), abstain=both.mean(), empty=empty.mean(),
                             risk_only=risk_only.mean(), safe_only=safe_only.mean(),
                             fall_in_risk=yt[risk_only].mean() if risk_only.any() else np.nan,
                             fall_in_safe=yt[safe_only].mean() if safe_only.any() else np.nan,
                             fall_in_abstain=yt[both].mean() if both.any() else np.nan, base=yt.mean(), n_cal=int(iv.sum())))
        print(k, 'M-C', {a_: round(b_, 3) for a_, b_ in out['C'][-1].items() if isinstance(b_, float)}, flush=True)
    print(k, 'done', round(time.time() - t0), 's', flush=True)
for kk in out: out[kk] = pd.DataFrame(out[kk])
if 'A' in SEL:
    A = out['A']; out['A_verdict'] = '성공' if ((A.ratio >= 2) & (A.p < 0.001)).all() else '실패'
if 'B' in SEL:
    B = out['B']; ok = ((B.auc_adaptive >= B.auc_fixed12 - 0.005) & (B.q_mean < 12)).sum(); out['B_verdict'] = '성공' if ok >= 4 else '실패'; out['B_ok'] = int(ok)
if 'C' in SEL:
    C = out['C']; ok = ((C.cov_pos >= 0.88) & (C.cov_neg >= 0.88)).sum(); out['C_verdict'] = '성공' if ok >= 4 else '실패'; out['C_ok'] = int(ok)
print({k_: v for k_, v in out.items() if 'verdict' in k_ or k_.endswith('_ok')})
pickle.dump(out, open(W + f'mabc_out_{"".join(SEL)}.pkl', 'wb'))
