"""정답 v3 (노트 원칙): 가처분소득 · 반복 관측(1~4년 뒤 3번 중 2번 이상) · 조사별 역할 분담.
정답 패널: 복지·재정·국민노후(가처분소득 보유). 노동패널 = 재현용(경상소득). 국민노후 = 생활비 기준선 정답 추가."""
import numpy as np, pandas as pd, pickle, warnings
from common_ml import *
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import lightgbm as lgb
warnings.filterwarnings('ignore')
cpi = pd.read_csv('/mnt/user-data/attachments/e5872982-71a4-5f1c-953f-30befae32eac/6ab02c44-7_cpi_kosis_2020eq100.csv').set_index('year').cpi
defl = cpi[2023] / cpi
# ---- 가처분 빈곤선: 복지패널 전 연령 가중 중위 균등화 가처분소득의 50% ----
A = pd.read_pickle(W + 'koweps_all_ages.pkl').dropna(subset=['h_din', 'h01_1']); A = A[A.h01_1 > 0]
A['e'] = A.h_din / np.sqrt(A.h01_1) * A.year.map(defl)
def wmed(g):
    g = g.dropna(subset=['e']); w = g['p_wsc'].fillna(g['p_wsc'].median()).values; o = np.argsort(g['e'].values)
    cw = np.cumsum(w[o]); return g['e'].values[o][np.searchsorted(cw, cw[-1] / 2)]
dline = 0.5 * A.groupby('year')[['e', 'p_wsc']].apply(wmed); dline[2004] = dline[2005]
print('가처분 빈곤선:', dline.round(0).to_dict())

key = ['panel', 'pid', 'svy_year']
P = pd.concat([pd.read_pickle(W + f'p_{p}.pkl') for p in ['koweps', 'nastab', 'kreis', 'klips', 'khp', 'klosa']], ignore_index=True)
P = P[P.inc_year.between(2004, 2025)].sort_values(key).drop_duplicates(key)
P['hhsize'] = P.groupby(['panel', 'pid']).hhsize.transform(lambda s: s.ffill().bfill()).fillna(2).clip(1, 10)
P['line_d'] = P.inc_year.map(dline)
NODIS = P.panel.isin(['KLIPS', 'KHP', 'KLoSA'])
inc = np.where(NODIS, P.hhinc, P.hhdin)          # 노동패널은 가처분소득이 없어 경상소득(재현용)
P['line_use'] = np.where(NODIS, P.inc_year.map(pd.read_csv(W + 'poverty_line.csv').set_index('year').line), P.line_d)
P['r'] = (inc / np.sqrt(P.hhsize) * P.inc_year.map(defl)) / P.line_use
P.loc[~(inc > 0), 'r'] = np.nan
# 국민노후: 연도·가구유형(부부/개인)별 '필요 최소 노후생활비' 응답 중위값을 기준선으로 (월, 만원)
K = P.panel == 'KReIS'
P['need_type'] = np.where(P.married == 1, 'couple', 'single')
needmed = P[K & P.x_need_min.notna()].groupby(['svy_year', 'need_type']).x_need_min.median()
P['need_line'] = [needmed.get((y, t), np.nan) for y, t in zip(P.svy_year, P.need_type)]
P['rn'] = np.where(K, (P.hhdin / 12) / P.need_line * defl.reindex(P.inc_year).values / defl.reindex(P.inc_year).values, np.nan)
P.loc[K & ~(P.hhdin > 0), 'rn'] = np.nan
fut = {}
for k in [1, 2, 3, 4]:
    o = P[key + ['r', 'rn']].copy(); o['svy_year'] -= k; fut[k] = o.rename(columns={'r': f'r_f{k}', 'rn': f'rn_f{k}'})
lag = P[key + ['r']].copy(); lag['svy_year'] += 2; lag = lag.rename(columns={'r': 'r_l2'})
F = P[key + ['r', 'rn']].copy()
for k in fut: F = F.merge(fut[k], on=key, how='left')
F = F.merge(lag, on=key, how='left')
SA = pd.read_pickle(W + 'analytic_all.pkl')   # 공통·추가 입력(이력 변수 포함)
D0 = SA.merge(F, on=key, how='inner', suffixes=('', '_v3'))
D0['log_dratio'] = np.log(D0.r.where(D0.r > 0))
D0['d_log_dratio_2y'] = D0.log_dratio - np.log(D0.r_l2.where(D0.r_l2 > 0))
D0['log_rneed'] = np.log(pd.Series(D0.rn).where(D0.rn > 0))
D0.to_pickle(W + 'v3_D0.pkl')


def label(D, base):
    f = {k: D[f'{base}_f{k}'] for k in [2, 3, 4]}
    obs = sum(f[k].notna().astype(int) for k in f); below = sum((f[k] < 1).astype(int) for k in f)
    ok = f[2].notna() & f[4].notna()
    y = np.where(f[3].notna(), below >= 2, (f[2] < 1) & (f[4] < 1))   # 3번 중 2번, 격년 조사는 2번 중 2번
    return ok, y.astype(int)


TASKS = []
for p in ['KOWEPS', 'NaSTaB', 'KReIS', 'KLIPS', 'KHP', 'KLoSA']:
    TASKS.append((p, 'r', 'log_dratio', '가처분 상대빈곤(중위 50%)' if p in ('KOWEPS', 'NaSTaB', 'KReIS') else
                  ('경상 상대빈곤(재현용)' if p == 'KLIPS' else '경상 상대빈곤(이식 검증용)')))
TASKS.append(('KReIS', 'rn', 'log_rneed', '필요 최소생활비 기준선'))
res, preds = [], {}
for p, base, b0col, nm in TASKS:
    d = D0[(D0.panel == p) & D0.age.between(50, 69)].copy()
    ok, y = label(d, base); d['y'] = y
    d = d[ok & (d[base] >= 1)]                         # 지금은 괜찮은 사람
    ys = sorted(d.svy_year.unique()); ty = ys[-2:]
    te = d[d.svy_year.isin(ty)].copy(); tr = d[d.svy_year <= min(ty) - 4].copy()
    EX = extra_features(tr); te = add_logs(te, EX)
    extra_inc = [c for c in ['log_dratio', 'd_log_dratio_2y', 'log_rneed'] if tr[c].notna().mean() > 0.2]
    cols = COMMON + EX + extra_inc
    X, Xt, yy = tr[cols].astype(float), te[cols].astype(float), tr.y.values
    vy = sorted(tr.svy_year.unique())[-2:]; iv = tr.svy_year.isin(vy).values; it = (tr.svy_year <= min(vy) - 4).values
    best = None
    for g in [dict(num_leaves=n, min_child_samples=m) for n in (15, 31) for m in (40, 150)]:
        m = lgb.LGBMClassifier(n_estimators=3000, learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                               reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=42, **g)
        m.fit(X[it], yy[it], eval_set=[(X[iv], yy[iv])], eval_metric='auc', callbacks=[lgb.early_stopping(100, verbose=False)])
        a = roc_auc_score(yy[iv], m.predict_proba(X[iv])[:, 1])
        if best is None or a > best[0]: best = (a, g, m.best_iteration_)
    m = lgb.LGBMClassifier(n_estimators=max(50, int(best[2] * 1.1)), learning_rate=0.03, subsample=0.8, subsample_freq=1,
                           colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=42, **best[1]).fit(X, yy)
    s_ml = m.predict_proba(Xt)[:, 1]
    s_lr = make_pipeline(SimpleImputer(add_indicator=True), StandardScaler(), LogisticRegression(max_iter=3000)).fit(X, yy).predict_proba(Xt)[:, 1]
    s_b0 = -te[b0col].values
    A_, B_, dl, se, pv_, _ = delong_diff(te.y.values, s_ml, s_b0)
    res.append(dict(panel=p, label=nm, n_tr=len(tr), n_te=len(te), persons_te=te.pid.nunique(), te_years=f'{ty[0]}·{ty[1]}',
                    pos_te=te.y.mean(), auc_b0=B_, auc_lr=roc_auc_score(te.y, s_lr), auc_ml=A_, delta=dl, se=se, p=pv_, inner=best[0]))
    pickle.dump((tr, te, cols), open(W + f'v3_data_{p}_{base}.pkl', 'wb'))
    preds[(p, nm)] = pd.DataFrame(dict(y=te.y.values, pid=te.pid.values, ml=s_ml, lr=s_lr, b0=s_b0))
    print(p, nm, 'train', len(tr), 'test', len(te), 'pos', round(te.y.mean(), 3), 'B0', round(B_, 3), 'LR', round(res[-1]['auc_lr'], 3),
          'ML', round(A_, 3), 'Δ', round(dl, 3), flush=True)
R = pd.DataFrame(res); R.to_csv(W + 'label_v3.csv', index=False); pickle.dump(preds, open(W + 'label_v3_preds.pkl', 'wb'))
g = R[R.label.str.startswith('가처분')]; m = meta_dl(g.delta, g.se)
print('가처분 3개 결합 Δ', round(m['est'], 4), round(m['lo'], 4), round(m['hi'], 4), 'mean ML', round(g.auc_ml.mean(), 3), 'B0', round(g.auc_b0.mean(), 3))
