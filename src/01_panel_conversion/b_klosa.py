"""고령화연구패널(KLoSA) Lt 요약파일 → 공통 스키마. 조사연도 2006+2(w-1), 소득은 전년도."""
import pandas as pd, numpy as np
out = []
for w in range(1, 10):
    d = pd.read_pickle(f'/home/claude/work/klosa_Lt0{w}_e.pkl').apply(pd.to_numeric, errors='coerce')
    p = f'w0{w}'
    g = lambda c: d[p + c] if p + c in d else pd.Series(np.nan, index=d.index)
    neg = lambda s: s.where(s >= 0)
    svy = 2006 + 2 * (w - 1)
    hh = d['hhid'] if 'hhid' in d else d['HHID']
    s = pd.DataFrame({
        'panel': 'KLoSA', 'pid': d.pid.astype('int64').astype(str), 'hid': hh.astype('int64').astype(str),
        'svy_year': svy, 'inc_year': svy - 1, 'age': g('A002_age'),
        'female': (g('gender1') == 5).astype(float),
        'edu3': np.select([g('edu') <= 2, g('edu') == 3], [0, 1], 2).astype(float),
        'married': (g('marital') == 1).astype(float), 'hhsize': g('hhsize'),
        'head': 1.0, 'hhinc': neg(g('hhinc')),
        'employed': (g('present_labor') == 1).astype(float).where(g('present_labor').isin([1, 5])),
        'w': g('wgt_c'),
        'x_health_bad': g('C001').where(g('C001').between(1, 5)),
        'x_chronic': neg(g('chronic_sum')),
        'x_adl': neg(g('adl')), 'x_iadl': neg(g('iadl')),
        'x_selfemp': g('status').isin([7]).astype(float),     # 7 자영업
        'x_regular': g('status').isin([1]).astype(float),     # 1 상용
        'x_temp_daily': g('status').isin([3, 5]).astype(float),
        'x_occ': neg(g('job')),
        'x_retired': neg(g('retired')),
        'x_pension_recv': (neg(g('national')).fillna(0) + neg(g('particular')).fillna(0) > 0).astype(float),
        'x_pension_amt': neg(g('national')).fillna(0) + neg(g('particular')).fillna(0),
        'x_own_earn': neg(g('earned')).fillna(0),
        'x_net_assets': g('hhnetassets') if p + 'hhnetassets' in d else g('pnetassets'),
        'x_fin_assets': neg(g('financialasset')).fillna(0),
        'x_debt': (g('hhliabilities') if p + 'hhliabilities' in d else g('pliabilities')),
        'x_owner': (g('f001type') == 1).astype(float),
        'x_transfer_from_children': neg(g('fromchildren')),
        'x_region': (g('region1') // 10),
    })
    out.append(s)
s = pd.concat(out, ignore_index=True)
s = s[s.age.between(45, 80)]
s.to_pickle('/home/claude/work/p_klosa.pkl')
print(s.shape); print(s.groupby('svy_year').size().to_dict())
print(s.describe().T[['count', 'mean', '50%']].to_string())
