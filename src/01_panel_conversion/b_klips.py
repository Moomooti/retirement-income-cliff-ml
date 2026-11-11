"""한국노동패널(KLIPS) → 공통 스키마. w차 조사연도 1997+w, 가구소득은 전년도(만원).
가구 경상소득 = 근로 + 금융(매매차익 제외) + 부동산(매매차익 제외) + 사회보험 + 이전소득."""
import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
D = '/home/claude/raw/2_KLIPS_1-27_stata/1-27#Ucc28 release  (Stata)/'
INC = ['2102', '2112', '2113', '2115', '2116', '2122', '2124', '2125', '2126', '2134', '2136', '2138', '2140', '2142',
       '2144', '2146', '2152', '2153', '2155', '2156', '2157', '2158', '2159', '2160']
FIN = ['2562', '2564', '2566', '2568', '2570', '2572']
DEBT = ['2602', '2605', '2608', '2611', '2614', '2617']
out = []
for w in range(8, 28):
    ww = f'{w:02d}'
    hc = set(pd.io.stata.StataReader(D + f'klips{ww}h.dta').variable_labels())
    hcols = [c for c in [f'hhid{ww}', f'h{ww}0150', f'h{ww}1406', f'h{ww}1412', f'w{ww}h'] +
             [f'h{ww}{k}' for k in INC + FIN + DEBT] if c in hc]
    h = pd.read_stata(D + f'klips{ww}h.dta', columns=hcols, convert_categoricals=False)
    pos = lambda s: s.where(s >= 0)
    h['hhinc'] = sum(pos(h[f'h{ww}{k}']).fillna(0) for k in INC if f'h{ww}{k}' in h)
    h['fin'] = sum(pos(h[f'h{ww}{k}']).fillna(0) for k in FIN if f'h{ww}{k}' in h)
    h['debt'] = sum(pos(h[f'h{ww}{k}']).fillna(0) for k in DEBT if f'h{ww}{k}' in h)
    pc = set(pd.io.stata.StataReader(D + f'klips{ww}p.dta').variable_labels())
    want = ['pid', f'hhid{ww}'] + [f'p{ww}{k}' for k in ['0101', '0102', '0107', '0110', '0121', '0211', '0314', '6101',
                                                         '2101', '0350', '0351', '0352', '1642', '1672']]
    p = pd.read_stata(D + f'klips{ww}p.dta', columns=[c for c in want if c in pc], convert_categoricals=False)
    for c in want:
        if c not in p: p[c] = np.nan
    d = p.merge(h, on=f'hhid{ww}', how='left')
    g = lambda k: d[f'p{ww}{k}']
    occ = g('0351').fillna(g('0352')).fillna(g('0350'))
    svy = 1997 + w
    st = g('0314')
    s = pd.DataFrame({
        'panel': 'KLIPS', 'pid': d.pid.astype('int64').astype(str), 'hid': d[f'hhid{ww}'].astype('int64').astype(str),
        'svy_year': svy, 'inc_year': svy - 1, 'age': g('0107'),
        'female': (g('0101') == 2).astype(float),
        'edu3': np.select([g('0110') <= 4, g('0110') == 5], [0, 1], 2).astype(float),
        'married': np.nan, 'hhsize': d[f'h{ww}0150'],
        'head': g('0102').isin([10, 20]).astype(float),
        'hhinc': d.hhinc, 'employed': g('0211').isin([1, 2, 3]).astype(float), 'w': d.get(f'w{ww}h'),
        'x_health_bad': g('6101').where(g('6101').between(1, 5)),
        'x_regular': (st == 1).astype(float), 'x_temp_daily': st.isin([2, 3]).astype(float),
        'x_selfemp': (st == 4).astype(float),
        'x_occ': pos(occ) // 100,
        'x_pension_enrolled': (g('2101') == 1).astype(float),
        'x_own_earn': 12 * (pos(g('1642')).fillna(0) + pos(g('1672')).fillna(0)),
        'x_fin_assets': d.fin, 'x_debt': d.debt,
        'x_owner': (d[f'h{ww}1406'] == 1).astype(float),
        'x_house_value': pos(d.get(f'h{ww}1412')).where(d[f'h{ww}1406'] == 1).fillna(0),
        'x_region': g('0121'),
    })
    s['rel'] = g('0102')
    out.append(s)
s = pd.concat(out, ignore_index=True)
# 배우자 유무: 같은 가구에 가구주(10)와 배우자(20)가 함께 있으면 가구주·배우자를 기혼으로 처리
sp = s.groupby(['hid', 'svy_year']).rel.transform(lambda r: (r == 20).any() & (r == 10).any())
s['married'] = (sp & s.rel.isin([10, 20])).astype(float)
s = s.drop(columns='rel')
s = s[s.age.between(45, 80)]
s.to_pickle('/home/claude/work/p_klips.pkl')
print(s.shape); print(s.groupby('svy_year').size().to_dict())
print(s.describe().T[['count', 'mean', '50%']].to_string())
