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

# ---------- 1. 가처분 빈곤선 (label_v3와 동일) ----------
A = pd.read_pickle(W + 'koweps_all_ages.pkl').dropna(subset=['h_din', 'h01_1']); A = A[A.h01_1 > 0]
A['e'] = A.h_din / np.sqrt(A.h01_1) * A.year.map(defl23)
def wmed(g):
    g = g.dropna(subset=['e']); w = g['p_wsc'].fillna(g['p_wsc'].median()).values; o = np.argsort(g['e'].values)
    cw = np.cumsum(w[o]); return g['e'].values[o][np.searchsorted(cw, cw[-1] / 2)]
dline = 0.5 * A.groupby('year')[['e', 'p_wsc']].apply(wmed); dline[2004] = dline[2005]

# ---------- 2. 복지패널 사는 집 가격 h06_6 ----------
H = []
for f in sorted(glob.glob('/home/claude/raw/3_KOWEPS_2005-2024_csv/raw/koweps_hp_w*.csv')):
    d = pd.read_csv(f, usecols=lambda c: c in ['h_id', 'year', 'h06_3', 'h06_6'] + [f'h10_aq{i}' for i in (1, 2, 3)], low_memory=False)
    H.append(d.drop_duplicates(['h_id', 'year']))
H = pd.concat(H, ignore_index=True)
miss = lambda s: s.where(~s.isin([9999999, 999999, 99999, 9999998]))
H['real_new'] = np.where(H.h06_3 == 1, miss(H.h06_6).fillna(0), 0) + sum(miss(H[f'h10_aq{i}']).fillna(0) for i in (1, 2, 3))
H = H.assign(hid=H.h_id.astype('int64').astype(str), inc_year=H.year.astype(int))[['hid', 'inc_year', 'real_new']]

# ---------- 3. 사람×연도 기본 표 + 1·2년 전 ----------
P = pd.concat([pd.read_pickle(W + f'p_{p}.pkl') for p in ['koweps', 'nastab']], ignore_index=True)
P = P[P.inc_year.between(2004, 2025)].sort_values(key).drop_duplicates(key)
P['hhsize'] = P.groupby(['panel', 'pid']).hhsize.transform(lambda s: s.ffill().bfill()).fillna(2).clip(1, 10)
P['r'] = P.hhdin / np.sqrt(P.hhsize) * P.inc_year.map(defl23) / P.inc_year.map(dline)
P.loc[~(P.hhdin > 0), 'r'] = np.nan
P = P.merge(H, on=['hid', 'inc_year'], how='left')
P.loc[P.panel != 'KOWEPS', 'real_new'] = np.nan
f25 = P.inc_year.map(to25); inc25 = P.hhdin * f25
for c, src in [('fin', 'x_fin_assets'), ('debt', 'x_debt'), ('real', 'real_new')]:
    amt = P[src] * f25 if src in P else np.nan
    P[f's_{c}_r'] = (amt / inc25).clip(-50, 200).where(P.hhdin > 0)
    P[f's_lg_{c}'] = np.sign(amt) * np.log1p(np.abs(amt))
def lagged(k, cols):
    o = P[key + cols].copy(); o['svy_year'] += k; return o.rename(columns={c: f'{c}_l{k}' for c in cols})
S = P.merge(lagged(1, ['r', 'employed']), on=key, how='left').merge(lagged(2, ['r', 'employed', 'hhsize']), on=key, how='left')
lr_ = lambda x: np.log(x.where(x > 0))
S['s_log_r'] = lr_(S.r)
S['s_d1'] = S.s_log_r - lr_(S.r_l1); S['s_d2'] = S.s_log_r - lr_(S.r_l2)
_h = np.log(S[['r', 'r_l1', 'r_l2']].where(lambda x: x > 0))
S['s_min3'] = _h.min(axis=1); S['s_vol3'] = _h.std(axis=1, ddof=0).where(_h.notna().sum(axis=1) >= 2)
S['s_lost'] = ((S.employed_l2 == 1) & (S.employed == 0)).astype(float).where(S.employed_l2.notna())
S['s_hhchg'] = S.hhsize - S.hhsize_l2
S['s_owner'] = S.get('x_owner'); S['s_health'] = S.get('x_health_bad')
SF = S[key + [c for c in S.columns if c.startswith('s_')] + ['employed_l1', 'employed_l2', 'r', 'r_l1', 'r_l2', 'hhdin']].rename(
    columns={'employed_l1': 's_emp_l1', 'employed_l2': 's_emp_l2', 'r': 'r_chk', 'hhdin': 'hhdin_chk', 'r_l1': 'rr_l1', 'r_l2': 'rr_l2'})
pickle.dump(dict(SF=SF, dline=dline), open(W + 's_features.pkl', 'wb'))

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


PRED = pickle.load(open(W + 'v3_pred.pkl', 'rb')); out = {}
for p, sets in [('KOWEPS', ['S20', 'S21']), ('NaSTaB', ['S20'])]:
    tr, te, _ = pickle.load(open(W + f'v3_data_{p}_r.pkl', 'rb')); tr, te = tr.reset_index(drop=True), te.reset_index(drop=True)
    tr = tr.merge(SF, on=key, how='left', validate='1:1'); te = te.merge(SF, on=key, how='left', validate='1:1')
    chk = np.nanmax(np.abs(np.log(te.r_chk) - te.log_dratio))
    print(p, 'r 일치 확인(최대 로그 차)', chk, '| 1년 전 소득 있음', round(te.rr_l1.notna().mean(), 3), '| 2년 전', round(te.rr_l2.notna().mean(), 3), flush=True)
    full = PRED[f'{p}_r']['최종: LightGBM+로지스틱'].values; yt = te.y.values; pid = te.pid.values; b0 = -te.s_log_r.values
    for sn in sets:
        cols = [c for c in SETS[sn] if c in tr and tr[c].notna().mean() > 0.2 and tr[c].nunique() > 1]
        t0 = time.time(); M = fit_set(tr, te, cols)
        sg, sl, fin, ref, Xt = score(M, te)
        a_full, a_s, a_g, a_l = roc_auc_score(yt, full), roc_auc_score(yt, fin), roc_auc_score(yt, sg), roc_auc_score(yt, sl)
        d, lo, hi = boot_diff(yt, full, fin, pid)
        _, _, dd, se, pv, _ = delong_diff(yt, fin, b0)
        ok1 = (a_full - a_s) <= 0.01 and hi <= 0.02; ok2 = dd - 1.96 * se > 0
        s_c = M['mc'].predict_proba(Xt)[:, 1]; inc1 = (1 - s_c) <= M['q1']; inc0 = s_c <= M['q0']
        cov = dict(cov_pos=float(inc1[yt == 1].mean()), cov_neg=float(inc0[yt == 0].mean()), abstain=float((inc1 & inc0).mean()))
        r = dict(panel=p, set=sn, n_feat=len(cols), cols=cols, n_tr=len(tr), n_te=len(te), auc_full=a_full, auc_service=a_s, auc_lgb=a_g, auc_lr=a_l,
                 auc_b0=roc_auc_score(yt, b0), loss=a_full - a_s, loss_boot=d, loss_lo=lo, loss_hi=hi, vs_b0=dd, vs_b0_lo=dd - 1.96 * se,
                 pass1=ok1, pass2=ok2, inner=M['inner'], params=M['params'], iters=M['iters'], **cov, sec=round(time.time() - t0))
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k != 'cols'}, flush=True)
        out[(p, sn)] = dict(res=r, M=M, ref=ref, te_keys=te[key].copy())
        # ----- 회상 소득 민감도 (복지 S20만) -----
        if p == 'KOWEPS' and sn == 'S20':
            sens = []
            for nm, kind, v in [('잡음 ±20%', 'noise', 0.2), ('잡음 ±40%', 'noise', 0.4), ('아래 치우침 −10%', 'bias', 0.9), ('아래 치우침 −20%', 'bias', 0.8)]:
                aucs = []
                for rep in range(20 if kind == 'noise' else 1):
                    rng = np.random.RandomState(rep); T = te.copy()
                    if kind == 'noise': m1, m2 = rng.uniform(1 - v, 1 + v, len(T)), rng.uniform(1 - v, 1 + v, len(T))
                    else: m1 = m2 = np.full(len(T), v)
                    T['rr_l1'] = T.rr_l1 * m1; T['rr_l2'] = T.rr_l2 * m2
                    T['s_d1'] = T.s_log_r - lr_(T.rr_l1); T['s_d2'] = T.s_log_r - lr_(T.rr_l2)
                    h = np.log(T[['r_chk', 'rr_l1', 'rr_l2']].where(lambda x: x > 0)); T['s_min3'] = h.min(axis=1)
                    T['s_vol3'] = h.std(axis=1, ddof=0).where(h.notna().sum(axis=1) >= 2)
                    aucs.append(roc_auc_score(yt, score(M, T, ref)[2]))
                sens.append(dict(cond=nm, auc=np.mean(aucs), drop=a_s - np.mean(aucs), sd=np.std(aucs)))
            out['sens'] = pd.DataFrame(sens); out['sens_ok'] = bool(out['sens']['drop'].iloc[0] <= 0.01)
            print(out['sens'].round(4), flush=True)
pickle.dump(out, open(W + 's_out.pkl', 'wb'))
print('done')
