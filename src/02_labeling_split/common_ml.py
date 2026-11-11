"""공통: 분할, 특성 목록, 전처리, DeLong."""
import numpy as np, pandas as pd
from scipy import stats

W = '/home/claude/work/'
PANELS = ['KOWEPS', 'KLIPS', 'NaSTaB', 'KHP', 'KLoSA', 'KReIS']
NAME = {'KOWEPS': '한국복지패널', 'KLIPS': '한국노동패널', 'NaSTaB': '재정패널', 'KHP': '한국의료패널',
        'KLoSA': '고령화연구패널', 'KReIS': '국민노후보장패널'}
# 사전 등록: 각 패널의 최근 2개 기준 차수 = 테스트. 학습은 결과 시점이 테스트 시작 이전인 행만.
TEST_YEARS = {'KOWEPS': [2022, 2023], 'KLIPS': [2021, 2022], 'NaSTaB': [2021, 2022], 'KHP': [2022, 2023],
              'KLoSA': [2018, 2020], 'KReIS': [2019, 2021]}

COMMON = ['log_ratio', 'age', 'age_to_60', 'age_to_nps', 'female', 'edu3', 'married', 'hhsize', 'employed',
          'd_log_ratio_2y', 'd_log_ratio_4y', 'vol_hist', 'min_ratio_hist', 'ever_below_hist', 'lost_job_2y', 'hh_change_2y', 'employed_l2']
CATEG = ['x_occ', 'x_region', 'x_pension_type', 'x_health_ins']
EXCL = {'x_own_earn', 'x_fin_assets', 'x_net_assets', 'x_debt', 'x_realestate', 'x_house_value', 'x_pension_amt',
        'x_ast_he001', 'x_ast_he002', 'x_ast_he003', 'x_ast_he004', 'x_src_hd004', 'x_src_hd005', 'x_src_hd006',
        'x_src_hd007', 'x_src_hd008', 'x_src_hd009', 'x_transfer_from_children',
        'x_hh_earn', 'x_pub_transfer', 'x_priv_transfer', 'x_fin_income'}   # 원금액 대신 소득 대비 배수(_r)와 로그 사용


def split(S, p):
    d = S[S.panel == p]
    ty = TEST_YEARS[p]
    te = d[d.svy_year.isin(ty)]
    tr = d[d.svy_year <= min(ty) - 2]
    return tr.copy(), te.copy()


def extra_features(tr):
    xs = []
    for c in tr.columns:
        if (c.startswith('x_') and c not in EXCL) or c in ('d_log_ratio_1y', 'employed_l1'):
            v = tr[c]
            if v.notna().mean() >= 0.2 and v.nunique(dropna=True) > 1:
                xs.append(c)
    # 자산·부채 원금액은 로그 변환해서 추가
    for c in ['x_fin_assets', 'x_net_assets', 'x_debt', 'x_house_value', 'x_realestate']:
        if c in tr and tr[c].notna().mean() >= 0.2 and tr[c].nunique() > 1:
            tr['lg_' + c] = np.sign(tr[c]) * np.log1p(np.abs(tr[c]))
            xs.append('lg_' + c)
    return xs


def add_logs(df, feats):
    for f in feats:
        if f.startswith('lg_') and f not in df:
            c = f[3:]; df[f] = np.sign(df[c]) * np.log1p(np.abs(df[c]))
    return df


# ---------- DeLong (Sun & Xu 2014) ----------
def _midrank(x):
    J = np.argsort(x); Z = x[J]; N = len(x); T = np.zeros(N); i = 0
    while i < N:
        j = i
        while j < N and Z[j] == Z[i]: j += 1
        T[i:j] = 0.5 * (i + j - 1) + 1; i = j
    T2 = np.empty(N); T2[J] = T; return T2


def delong(y, *scores):
    y = np.asarray(y).astype(bool); m = y.sum(); n = (~y).sum()
    k = len(scores); aucs = np.zeros(k); V10 = np.zeros((k, m)); V01 = np.zeros((k, n))
    for r, s in enumerate(scores):
        s = np.asarray(s, float); pos, neg = s[y], s[~y]
        tx, ty, tz = _midrank(pos), _midrank(neg), _midrank(np.r_[pos, neg])
        aucs[r] = (tz[:m].sum() - m * (m + 1) / 2) / (m * n)
        V10[r] = (tz[:m] - tx) / n
        V01[r] = 1 - (tz[m:] - ty) / m
    S = np.atleast_2d(np.cov(V10)) / m + np.atleast_2d(np.cov(V01)) / n
    return aucs, S


def delong_diff(y, a, b):
    aucs, S = delong(y, a, b)
    d = aucs[0] - aucs[1]; se = np.sqrt(S[0, 0] + S[1, 1] - 2 * S[0, 1])
    z = d / se; p = 2 * stats.norm.sf(abs(z))
    return aucs[0], aucs[1], d, se, p, np.sqrt(S[0, 0])


def meta_dl(est, se):
    est, se = np.asarray(est), np.asarray(se); w = 1 / se ** 2
    fe = (w * est).sum() / w.sum(); Q = (w * (est - fe) ** 2).sum(); k = len(est)
    tau2 = max(0, (Q - (k - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
    wr = 1 / (se ** 2 + tau2); re = (wr * est).sum() / wr.sum(); sre = np.sqrt(1 / wr.sum())
    I2 = max(0, (Q - (k - 1)) / Q) if Q > 0 else 0
    return dict(est=re, se=sre, lo=re - 1.96 * sre, hi=re + 1.96 * sre, p=2 * stats.norm.sf(abs(re / sre)),
                tau2=tau2, I2=I2, Q=Q, fe=fe)
