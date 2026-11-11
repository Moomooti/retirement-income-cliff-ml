"""6개 패널 공통 정의 적용.
- 실질 균등화 가구소득 = 가구 경상소득 / sqrt(가구원수) × CPI(2023)/CPI(소득연도)   [2023년 가격, 만원]
- 빈곤선(line) = 복지패널 전 연령 가중 중위 균등화 경상소득의 50% (소득연도별, 2023년 가격)
- 분석 단위: 50~69세, 사람 × 조사차수 t, t 시점 소득 ≥ 빈곤선 (지금은 괜찮음), t+2년 조사에서 소득 관측
- 정답 y = t+2년 균등화소득 < 그 해 빈곤선
"""
import pandas as pd, numpy as np
W = '/home/claude/work/'
cpi = pd.read_csv('/mnt/user-data/attachments/e5872982-71a4-5f1c-953f-30befae32eac/6ab02c44-7_cpi_kosis_2020eq100.csv').set_index('year').cpi
defl = cpi[2023] / cpi

# ---- 전국 빈곤선 (KOWEPS 전 연령, 사람 가중) ----
A = pd.read_pickle(W + 'koweps_all_ages.pkl').dropna(subset=['h_cin', 'h01_1'])
A = A[A.h01_1 > 0]
A['eqinc'] = A.h_cin / np.sqrt(A.h01_1) * A.year.map(defl)
def wmed(g):
    g = g.dropna(subset=['eqinc']); w = g['p_wsc'].fillna(g['p_wsc'].median()); o = np.argsort(g['eqinc'].values)
    cw = np.cumsum(w.values[o]); return g['eqinc'].values[o][np.searchsorted(cw, cw[-1] / 2)]
med = A.groupby('year')[['eqinc','p_wsc']].apply(wmed)
med[2004] = med[2005]
med = med.sort_index()
line = 0.5 * med
line.to_csv(W + 'poverty_line.csv', header=['line'])
print('빈곤선(2023년 가격, 만원/년):'); print(line.round(0).to_dict())

P = pd.concat([pd.read_pickle(W + f'p_{p}.pkl') for p in ['koweps', 'klips', 'nastab', 'khp', 'klosa', 'kreis']],
              ignore_index=True)
P = P[P.inc_year.between(2004, 2025)]
P.loc[P.panel == 'KHP', 'x_chronic'] = (P.loc[P.panel == 'KHP', 'x_chronic'] > 0).astype(float)
P = P.sort_values(['panel', 'pid', 'svy_year'])
P['hhsize'] = P.groupby(['panel', 'pid']).hhsize.transform(lambda s: s.ffill().bfill()).fillna(2).clip(1, 10)
P = P.drop_duplicates(['panel', 'pid', 'svy_year'])
P['eqinc'] = P.hhinc / np.sqrt(P.hhsize) * P.inc_year.map(defl)
P['line'] = P.inc_year.map(line)
P['ratio'] = P['eqinc'] / P['line']
P['below'] = (P.ratio < 1).astype(float).where(P['eqinc'].notna())

key = ['panel', 'pid', 'svy_year']
def shift(df, k, cols, suf):
    o = df[['panel', 'pid', 'svy_year'] + cols].copy(); o['svy_year'] = o.svy_year - k  # o는 t+k 값을 t에 붙임
    return o.rename(columns={c: c + suf for c in cols})
lagcols = ['ratio', 'employed', 'below', 'hhsize', 'married', 'x_health_bad', 'x_own_earn', 'hhinc']
lagcols = [c for c in lagcols if c in P]
# 결과(t+2)
F = P.merge(shift(P, 2, ['ratio', 'below', 'eqinc', 'line'], '_f2'), on=key, how='left')
F = F.merge(shift(P, 4, ['ratio'], '_f4'), on=key, how='left').merge(shift(P, 1, ['ratio'], '_f1'), on=key, how='left').merge(shift(P, 3, ['ratio'], '_f3'), on=key, how='left')
# 이력(t-2, t-1): 아래로 2/1년 이동
L2 = P[key + lagcols].copy(); L2['svy_year'] += 2; L2 = L2.rename(columns={c: c + '_l2' for c in lagcols})
L1 = P[key + ['ratio', 'employed']].copy(); L1['svy_year'] += 1; L1 = L1.rename(columns={'ratio': 'ratio_l1', 'employed': 'employed_l1'})
F = F.merge(L2, on=key, how='left').merge(L1, on=key, how='left')
# 지난 2개 차수(4년)까지의 최저 소득비, 과거 빈곤 경험
L4 = P[key + ['ratio', 'below']].copy(); L4['svy_year'] += 4; L4 = L4.rename(columns={'ratio': 'ratio_l4', 'below': 'below_l4'})
F = F.merge(L4, on=key, how='left')

S = F[F.age.between(50, 69) & F.ratio_f2.notna() & (F.hhinc > 0)].copy()   # 상태형 비교용으로 일단 전원
S['y'] = (S.ratio_f2 < 1).astype(int)

# ---- 파생 변수 ----
S['log_ratio'] = np.log(S.ratio)
S['d_log_ratio_2y'] = S.log_ratio - np.log(S.ratio_l2.where(S.ratio_l2 > 0))
S['d_log_ratio_1y'] = S.log_ratio - np.log(S.ratio_l1.where(S.ratio_l1 > 0))
S['min_ratio_hist'] = np.log(S[['ratio', 'ratio_l2', 'ratio_l4']].where(lambda x: x > 0).min(axis=1))
S['d_log_ratio_4y'] = S.log_ratio - np.log(S.ratio_l4.where(S.ratio_l4 > 0))
_h = np.log(S[['ratio', 'ratio_l2', 'ratio_l4']].where(lambda x: x > 0))
S['vol_hist'] = _h.std(axis=1, ddof=0).where(_h.notna().sum(axis=1) >= 2)
S['ever_below_hist'] = S[['below_l2', 'below_l4']].max(axis=1)
S['lost_job_2y'] = ((S.employed_l2 == 1) & (S.employed == 0)).astype(float).where(S.employed_l2.notna())
S['hh_change_2y'] = (S.hhsize - S.hhsize_l2)
S['age_to_60'] = S.age - 60          # 정년 60세 기준 거리
S['age_to_nps'] = S.age - np.select([S.inc_year + 1 - S.age <= 1952, S.inc_year + 1 - S.age <= 1956,
                                     S.inc_year + 1 - S.age <= 1960, S.inc_year + 1 - S.age <= 1964,
                                     S.inc_year + 1 - S.age <= 1968], [60, 61, 62, 63, 64], 65)  # 국민연금 수급개시연령까지
if 'x_own_earn' in S:
    S['x_earn_share'] = (S.x_own_earn / S.hhinc).clip(0, 1.5)
for c in ['x_fin_assets', 'x_net_assets', 'x_debt', 'x_realestate', 'x_house_value', 'x_ast_he001', 'x_ast_he002',
          'x_ast_he003', 'x_ast_he004', 'x_pension_amt', 'x_src_hd004', 'x_src_hd007', 'x_src_hd008', 'x_transfer_from_children',
          'x_hh_earn', 'x_pub_transfer', 'x_priv_transfer', 'x_fin_income']:
    if c in S:
        S[c + '_r'] = (S[c] / S.hhinc).clip(-50, 200)   # 소득 대비 배수
S['x_health_bad_d2'] = S['x_health_bad'] - S['x_health_bad_l2']
S.to_pickle(W + 'analytic_all.pkl')          # 상태형(지금 가난한 사람 포함)
S = S[S.ratio >= 1].copy()                     # 변화형 주분석: 지금은 빈곤선 이상
S.to_pickle(W + 'analytic.pkl')
print(S.shape)
print(S.groupby('panel').agg(n=('y', 'size'), pos=('y', 'mean'), persons=('pid', 'nunique'),
                             yr0=('svy_year', 'min'), yr1=('svy_year', 'max')).to_string())
print(S.groupby(['panel', 'svy_year']).y.agg(['size', 'mean']).unstack(0).round(3).to_string())
