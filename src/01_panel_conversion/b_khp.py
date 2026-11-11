"""한국의료패널(KHP) → 공통 스키마. 1기(2008~2018)와 2기(2019~2024)는 ID가 이어지지 않아 따로 추적.
연도 = 자료 기준연도(소득 기준연도와 동일하게 취급), 금액 만원."""
import pandas as pd, numpy as np, warnings, os
warnings.filterwarnings('ignore')
B = '/home/claude/raw/5_KHP_2008-2024/khp/'
def rd(f, **k):
    d = pd.read_stata(f, convert_categoricals=False)
    if '/t' in f.split('KHP')[-1]: d.columns = [c.upper() if c.upper() not in ('CD',) else c for c in d.columns]
    if 'columns' in k: d = d[k['columns']]
    return d
out = []
# ---- 1기 ----
for y in range(2008, 2019):
    yy = f'{y % 100:02d}'
    i = rd(B + f'KHP{y}/t{yy}ind.dta')
    h = rd(B + f'KHP{y}/t{yy}hh.dta')
    i = i.merge(h[['HHID', 'TOTAL', 'B1', 'B7']], on='HHID', how='left')
    try:
        inc = rd(B + f'KHP{y}/t{yy}income_ind.dta')[['PIDWON', 'G1']].groupby('PIDWON').G1.sum()
        i['own'] = i.PIDWON.map(inc)
    except Exception:
        i['own'] = np.nan
    try:
        cd = rd(B + f'KHP{y}/t{yy}cd.dta', columns=['PIDWON'])
        i['nchron'] = i.PIDWON.map(cd.PIDWON.value_counts()).fillna(0)
    except Exception:
        i['nchron'] = np.nan
    e = i.C8
    tens = np.where(e >= 10, e // 10, 0)
    st = i.get('C33', pd.Series(np.nan, index=i.index))
    if 'C15' not in i: i['C15'] = np.nan
    s = pd.DataFrame({
        'panel': 'KHP', 'pid': 'A' + i.PIDWON.astype('int64').astype(str), 'hid': 'A' + i.HHIDWON.astype('int64').astype(str),
        'inc_year': y, 'svy_year': y + 1, 'age': y - i.C4_0, 'female': (i.C3 == 2).astype(float),
        'edu3': np.select([tens <= 2, tens == 3], [0, 1], 2).astype(float),
        'married': (i.C7 == 1).astype(float), 'hhsize': i.B1, 'head': np.nan,
        'hhinc': i.TOTAL, 'employed': (i.C24 == 1).astype(float).where(i.C24.isin([1, 2])),
        'w': i.get('I_WGC_08'),
        'x_chronic': i.nchron,
        'x_regular': (st == 1).astype(float), 'x_temp_daily': st.isin([2, 3]).astype(float),
        'x_selfemp': st.isin([4, 5]).astype(float),
        'x_pension_enrolled': (i.C15 == 1).astype(float).where(i.C15 > 0),
        'x_pension_recv': (i.C15 == 3).astype(float).where(i.C15 > 0),
        'x_own_earn': i.own.where(i.own >= 0).fillna(0),
        'x_owner': (i.B7 == 1).astype(float),
        'phase': 1,
    })
    out.append(s)
# ---- 2기 ----
for y, L in zip(range(2019, 2025), 'abcdef'):
    i = rd(B + f'KHP{y}/{L}_ind.dta')
    h = rd(B + f'KHP{y}/{L}_hh.dta')
    i = i.merge(h[['hhid', 'fam_n', 'debt', 'prop']], on='hhid', how='left')
    s = pd.DataFrame({
        'panel': 'KHP', 'pid': 'B' + i.pidwon.astype('int64').astype(str), 'hid': 'B' + i.hhid.astype('int64').astype(str),
        'inc_year': y, 'svy_year': y + 1, 'age': y - i.birth_y, 'female': (i.sex == 2).astype(float),
        'edu3': np.select([i.edu <= 3, i.edu == 4], [0, 1], 2).astype(float),
        'married': (i.marr == 1).astype(float), 'hhsize': i.fam_n,
        'head': i.hh_rel.isin([10, 20]).astype(float),
        'hhinc': i.h_inc_tot, 'employed': (i.eco1 == 1).astype(float).where(i.eco1.notna()),
        'w': i.get('i_wgc'),
        'x_chronic': (i.cd == 1).astype(float).where(i.cd.isin([1, 2])),
        'x_health_bad': i.hs_srh.where(i.hs_srh.between(1, 5)) if 'hs_srh' in i else np.nan,
        'x_disability': (i.disa_yn == 1).astype(float),
        'x_regular': (i.eco2 == 1).astype(float), 'x_temp_daily': (i.eco2 == 2).astype(float),
        'x_selfemp': (i.eco2 == 3).astype(float),
        'x_own_earn': i.i_inc1.where(i.i_inc1 >= 0).fillna(0) + i.i_inc2.where(i.i_inc2 >= 0).fillna(0),
        'x_net_assets': i.prop - i.debt, 'x_debt': i.debt,
        'x_health_ins': i.health_ins,
        'x_region': i.region1,
        'phase': 2,
    })
    out.append(s)
s = pd.concat(out, ignore_index=True)
s = s[s.age.between(45, 80)]
s.to_pickle('/home/claude/work/p_khp.pkl')
print(s.shape); print(s.groupby('inc_year').size().to_dict())
print(s.describe().T[['count', 'mean', '50%']].to_string())
