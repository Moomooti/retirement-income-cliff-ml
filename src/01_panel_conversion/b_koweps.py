"""한국복지패널(KOWEPS) → 공통 스키마. 금액 단위 만원, 연도 = 소득 기준연도."""
import pandas as pd, numpy as np, glob, sys
RAW = '/home/claude/raw/3_KOWEPS_2005-2024_csv/raw'
cols = ['h_pid','h_id','year','h_g2','h_g3','h_g4','h_g6','h_g10','h_eco4','h_eco9','h_eco5_1','h_med2',
        'h_g9_1','h_soc_2','h_soc_12','h_soc10','h_cin','h_din','h01_1','h_reg7','p01_1','p_wsc','h_pers_income1',
        'h_pers_income2','h_pers_income3','h_pers_income5','h06_3'] + \
       [f'h09_aq{i}' for i in range(1,7)] + [f'h10_aq{i}' for i in range(1,11)]
out = []
allinc = []
for f in sorted(glob.glob(f'{RAW}/koweps_hp_w*.csv')):
    d = pd.read_csv(f, usecols=lambda c: c in cols, low_memory=False)
    for c in cols:
        if c not in d: d[c] = np.nan
    # 전 연령 가구 균등화 경상소득 (전국 중위소득 산출용)
    a = d[['year','h_id','h_cin','h_din','h01_1','p_wsc']].copy()
    allinc.append(a)
    d['age'] = d.year - d.h_g4
    d = d[d.age.between(45, 75)]
    out.append(d)
d = pd.concat(out, ignore_index=True)
A = pd.concat(allinc, ignore_index=True)
A.to_pickle('/home/claude/work/koweps_all_ages.pkl')

def miss(s, codes=(9999999, 999999, 99999, 9999998)):
    return s.where(~s.isin(codes))
debt = sum(miss(d[f'h09_aq{i}']).fillna(0) for i in range(1, 7))
fin = sum(miss(d[f'h10_aq{i}']).fillna(0) for i in range(6, 11))
re_ = sum(miss(d[f'h10_aq{i}']).fillna(0) for i in range(1, 6))
own_earn = sum(d[c].fillna(0) for c in ['h_pers_income1','h_pers_income2','h_pers_income3','h_pers_income5'])
s = pd.DataFrame({
    'panel': 'KOWEPS', 'pid': d.h_pid.astype('int64').astype(str), 'hid': d.h_id.astype('int64').astype(str),
    'inc_year': d.year.astype(int), 'svy_year': d.year.astype(int) + 1,
    'age': d.age, 'female': (d.h_g3 == 2).astype(float),
    'edu3': np.select([d.h_g6 <= 4, d.h_g6 == 5], [0, 1], 2).astype(float),
    'married': (d.h_g10 == 1).astype(float), 'hhsize': d.h01_1,
    'head': d.h_g2.isin([10, 20]).astype(float),
    'hhinc': d.h_cin, 'hhdin': d.h_din, 'employed': d.h_eco4.between(1, 7).astype(float).where(d.h_eco4.notna()),
    'w': d.p_wsc,
    # 조사별 추가 입력
    'x_health_bad': d.h_med2.where(d.h_med2.between(1, 5)),          # 1 매우건강 ~ 5 매우나쁨
    'x_chronic': (d.h_g9_1 == 3).astype(float),
    'x_selfemp': d.h_eco4.isin([5, 6]).astype(float),
    'x_temp_daily': d.h_eco4.isin([2, 3]).astype(float),
    'x_regular': (d.h_eco4 == 1).astype(float),
    'x_occ': d.h_eco9.where(d.h_eco9 > 0) // 100 if d.h_eco9.max() > 99 else d.h_eco9,
    'x_pension_recv': (d.p01_1 == 1).astype(float).where(d.p01_1.notna()),
    'x_pension_type': d.h_soc_2,
    'x_private_pension': (d.h_soc_12.isin([1, 2])).astype(float),
    'x_retire_pension': (d.h_soc10 == 1).astype(float),
    'x_own_earn': own_earn,
    'x_fin_assets': fin, 'x_realestate': re_, 'x_debt': debt,
    'x_owner': (d.h06_3 == 1).astype(float),
    'x_region': d.h_reg7,
})
s.to_pickle('/home/claude/work/p_koweps.pkl')
print(s.shape, s.inc_year.min(), s.inc_year.max())
print(s.describe().T[['count', 'mean', '50%']].to_string())
