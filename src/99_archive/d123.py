"""D1 인과 ML(AIPW) · D2 공정성 · D3 운영 시뮬레이션 (prereg_D123.txt)"""
import numpy as np, pandas as pd, pickle, warnings, sys
from scipy.stats import spearmanr
from common_ml import *
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
import lightgbm as lgb
warnings.filterwarnings('ignore')
SEL = sys.argv[1:] or ['D1', 'D2', 'D3']
PANS = ['KOWEPS', 'NaSTaB', 'KReIS', 'KLIPS']
small = lambda: lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=15, min_child_samples=50, subsample=0.8, subsample_freq=1,
                                   colsample_bytree=0.8, verbose=-1, n_jobs=2, random_state=42)
out = {}


def load(p):
    tr, te, cols = pickle.load(open(W + f'v3_data_{p}_r.pkl', 'rb'))
    return tr.reset_index(drop=True), te.reset_index(drop=True), cols


# ===================== D1 =====================
def aipw(X, A, Y, groups):
    n = len(Y); mu1, mu0, e = np.zeros(n), np.zeros(n), np.zeros(n)
    for a_, b_ in GroupKFold(5).split(X, A, groups):
        e[b_] = small().fit(X.iloc[a_], A[a_]).predict_proba(X.iloc[b_])[:, 1]
        t1 = a_[A[a_] == 1]; t0 = a_[A[a_] == 0]
        mu1[b_] = small().fit(X.iloc[t1], Y[t1]).predict_proba(X.iloc[b_])[:, 1]
        mu0[b_] = small().fit(X.iloc[t0], Y[t0]).predict_proba(X.iloc[b_])[:, 1]
    keep = (e > 0.02) & (e < 0.98)
    psi = (mu1 - mu0 + A * (Y - mu1) / np.clip(e, 1e-3, 1) - (1 - A) * (Y - mu0) / np.clip(1 - e, 1e-3, 1))[keep]
    ate = psi.mean(); g = pd.Series(psi - ate).groupby(np.asarray(groups)[keep]).sum()
    se = np.sqrt((g ** 2).sum()) / keep.sum()
    return ate, se, keep.mean(), e


if 'D1' in SEL:
    P = pd.concat([pd.read_pickle(W + f'p_{p}.pkl') for p in ['koweps', 'nastab', 'kreis', 'klips']])
    E = P[['panel', 'pid', 'svy_year', 'employed']].drop_duplicates(['panel', 'pid', 'svy_year']).copy(); E['svy_year'] -= 2
    E = E.rename(columns={'employed': 'emp_f2'})
    res = []
    for p in PANS:
        tr, te, cols = load(p); d = pd.concat([tr, te], ignore_index=True).merge(E, on=['panel', 'pid', 'svy_year'], how='left')
        d = d[(d.employed == 0) & d.emp_f2.notna()].reset_index(drop=True)
        A = (d.emp_f2 == 1).astype(int).values; Y = d.y.values.astype(int)
        hist = [c for c in cols if any(s in c for s in ['_l2', '_2y', '_4y', 'hist', '_l1', '_1y', 'lost_job'])]
        Xf = d[cols].astype(float); Xr = d[[c for c in cols if c not in hist]].astype(float)
        ate, se, ov, _ = aipw(Xf, A, Y, d.pid.values)
        ate_r, se_r, _, _ = aipw(Xr, A, Y, d.pid.values)
        pl = d.r_l2.notna().values
        Yp = (d.r_l2[pl] < 1).astype(int).values
        ate_p, se_p, ov_p, _ = aipw(Xr[pl].reset_index(drop=True), A[pl], Yp, d.pid.values[pl])
        raw = Y[A == 1].mean() - Y[A == 0].mean()
        r = dict(panel=p, n=len(d), treated=A.mean(), y_rate=Y.mean(), raw=raw, ate=ate, se=se, overlap=ov, ate_red=ate_r, se_red=se_r,
                 placebo=ate_p, se_placebo=se_p, n_placebo=int(pl.sum()))
        res.append(r); print('D1', {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    R = pd.DataFrame(res)
    def pool(est, se):
        w = 1 / se ** 2; m = (w * est).sum() / w.sum(); s = np.sqrt(1 / w.sum()); return m, m - 1.96 * s, m + 1.96 * s
    out['D1'] = R; out['D1_pool'] = pool(R.ate, R.se); out['D1_pool_red'] = pool(R.ate_red, R.se_red); out['D1_pool_placebo'] = pool(R.placebo, R.se_placebo)
    okc = out['D1_pool'][2] < 0; okp = out['D1_pool_placebo'][1] < 0 < out['D1_pool_placebo'][2]
    out['D1_verdict'] = '인과 근거 있음' if (okc and okp) else '인과 근거 불충분'
    print('D1 pooled', out['D1_pool'], 'placebo', out['D1_pool_placebo'], out['D1_verdict'], flush=True)

# ===================== D2 =====================
if 'D2' in SEL:
    PRED = pickle.load(open(W + 'v3_pred.pkl', 'rb')); rows = []
    for p in PANS:
        tr, te, cols = load(p); d = PRED[f'{p}_r']; y = d.y.values
        al = {}
        for nm, col in [('최종 모델', '최종: LightGBM+로지스틱'), ('지금 소득', 'B0 지금 소득')]:
            s = d[col].values; al[nm] = s >= np.quantile(s, 0.8)
        G = {'성별': {'남성': te.female == 0, '여성': te.female == 1}, '학력': {'고졸 미만': te.edu3 == 0, '고졸': te.edu3 == 1, '대졸 이상': te.edu3 == 2},
             '나이': {'50대': te.age < 60, '60대': te.age >= 60}, '가구': {'1인': te.hhsize == 1, '2인 이상': te.hhsize >= 2},
             '취업': {'취업': te.employed == 1, '미취업': te.employed == 0}}
        for dim, gs in G.items():
            for g, m in gs.items():
                m = m.values
                for nm, a in al.items():
                    pos, neg = m & (y == 1), m & (y == 0)
                    rows.append(dict(panel=p, dim=dim, group=g, model=nm, n=int(m.sum()), falls=int(pos.sum()),
                                     fnr=1 - a[pos].mean() if pos.sum() else np.nan, fpr=a[neg].mean() if neg.sum() else np.nan))
    F = pd.DataFrame(rows); out['D2'] = F
    gap = F.groupby(['panel', 'model', 'dim']).fnr.agg(lambda s: s.max() - s.min()).unstack('model')
    mx = gap.groupby('panel').max()
    ok_pan = (mx['최종 모델'] <= mx['지금 소득'] + 0.02).sum()
    piv = F.pivot_table(index=['panel', 'dim', 'group'], columns='model', values='fnr')
    share_better = (piv['최종 모델'] <= piv['지금 소득'] + 0.02).mean()
    out['D2_gap'] = gap; out['D2_maxgap'] = mx; out['D2_share'] = share_better
    out['D2_verdict'] = '악화 없음' if ok_pan >= 3 else '악화 있음'; out['D2_ok'] = int(ok_pan)
    print('D2', mx.round(3).to_dict(), 'share groups no worse', round(share_better, 3), out['D2_verdict'], flush=True)

# ===================== D3 =====================
if 'D3' in SEL:
    O = pickle.load(open(W + 'v3_out.pkl', 'rb')); IM = O['imp']; res = []
    for p, fixed_end in [('KOWEPS', 2010), ('KLIPS', 2009)]:
        tr, te, cols = load(p); d = pd.concat([tr, te], ignore_index=True)
        top = IM[IM.task == f'{p}_r'].sort_values('imp', ascending=False).feature.head(10).tolist()
        fx_tr = d[d.svy_year <= fixed_end - 4]
        mf = small().fit(fx_tr[cols].astype(float), fx_tr.y)
        def psi(a, b):
            v = []
            for c in top:
                x, z = a[c].dropna(), b[c].dropna()
                if x.nunique() < 3 or len(z) == 0: continue
                qs = np.unique(np.quantile(x, np.linspace(0, 1, 11))); qs[0], qs[-1] = -np.inf, np.inf
                pa = np.histogram(x, qs)[0] / len(x) + 1e-4; pb = np.histogram(z, qs)[0] / len(z) + 1e-4
                v.append(((pb - pa) * np.log(pb / pa)).sum())
            return np.mean(v) if v else np.nan
        for Y in sorted(d.svy_year.unique()):
            if Y < fixed_end: continue
            ev = d[d.svy_year == Y]
            if ev.y.sum() < 20: continue
            rt = d[d.svy_year <= Y - 4]; mr = small().fit(rt[cols].astype(float), rt.y)
            a_f = roc_auc_score(ev.y, mf.predict_proba(ev[cols].astype(float))[:, 1]); a_r = roc_auc_score(ev.y, mr.predict_proba(ev[cols].astype(float))[:, 1])
            res.append(dict(panel=p, year=Y, n_eval=len(ev), n_fixed=len(fx_tr), n_re=len(rt), auc_fixed=a_f, auc_re=a_r, gain=a_r - a_f,
                            psi=psi(fx_tr, ev), auc_b0=roc_auc_score(ev.y, -ev.log_dratio)))
            print('D3', res[-1], flush=True)
    R = pd.DataFrame(res); out['D3'] = R
    out['D3_gain'] = R.gain.mean(); out['D3_pos'] = (R.gain > 0).mean()
    out['D3_rho'] = spearmanr(R.psi, R.gain).correlation
    out['D3_verdict_re'] = '재학습 이득' if (R.gain.mean() > 0 and (R.gain > 0).mean() > 0.5) else '재학습 이득 없음'
    out['D3_verdict_alarm'] = '경보 유효' if out['D3_rho'] >= 0.5 else '경보 무효'
    print('D3', out['D3_gain'], out['D3_pos'], out['D3_rho'], out['D3_verdict_re'], out['D3_verdict_alarm'])
pickle.dump(out, open(W + f'd123_out_{"".join(SEL)}.pkl', 'wb'))
