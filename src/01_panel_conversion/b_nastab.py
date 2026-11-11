"""재정패널(NaSTaB) 차수별 가구/가구원 파일 → 공통 스키마. w차 조사연도 2007+w, 소득 2006+w (만원)."""
import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
H = '/home/claude/raw/4_NaSTaB_household_stata/NaSTaB{}H.dta'
P = '/home/claude/raw/4_NaSTaB_person_stata/NaSTaB{}P.dta'
out = []
for w in range(1, 18):
    ww = f'{w:02d}'
    rh = pd.io.stata.StataReader(H.format(ww)); hc = list(rh.variable_labels())
    fa = [c for c in hc if c in [f'h{ww}fa0{k}' for k in ('02', '04', '06', '08', '10', '12', '14', '18')]]
    hcols = [f'hid{ww}', f'h{ww}inc_a', f'h{ww}exp_b', f'w{ww}fnum', f'h{ww}fc001'] + fa + [c for c in [f'hs{ww}b10', f'h{ww}ba001'] if c in hc]
    h = pd.read_stata(H.format(ww), columns=hcols, convert_categoricals=False)
    rp = pd.io.stata.StataReader(P.format(ww)); pc = list(rp.variable_labels())
    want = [f'pid{ww}', f'hid{ww}', f'pw{ww}byr', f'pw{ww}gen', f'pw{ww}mar', f'pw{ww}edu', f'pw{ww}rel', f'pw{ww}jpo',
            f'pw{ww}job', f'p{ww}aa001', f'p{ww}bc001', f'p_{ww}_inc_bb1', f'p_{ww}_inc_bb2', f'p_{ww}_inc_ba1']
    p = pd.read_stata(P.format(ww), columns=[c for c in want if c in pc], convert_categoricals=False)
    for c in want:
        if c not in p: p[c] = np.nan
    d = p.merge(h, on=f'hid{ww}', how='left')
    g = lambda c: d[c] if c in d else pd.Series(np.nan, index=d.index)
    pos = lambda s: s.where(s >= 0)
    svy = 2007 + w
    jpo = g(f'pw{ww}jpo')
    aa = g(f'p{ww}aa001')
    emp = (aa == 1).astype(float).where(aa.isin([1, 2])) if aa.notna().any() else jpo.between(1, 6).astype(float)
    s = pd.DataFrame({
        'panel': 'NaSTaB', 'pid': d[f'pid{ww}'].astype('int64').astype(str), 'hid': d[f'hid{ww}'].astype('int64').astype(str),
        'svy_year': svy, 'inc_year': svy - 1, 'age': (svy - 1) - g(f'pw{ww}byr'),
        'female': (g(f'pw{ww}gen') == 2).astype(float),
        'edu3': np.select([g(f'pw{ww}edu') <= 3, g(f'pw{ww}edu') == 4], [0, 1], 2).astype(float),
        'married': (g(f'pw{ww}mar') == 1).astype(float), 'hhsize': g(f'w{ww}fnum'),
        'head': g(f'pw{ww}rel').isin([1, 2]).astype(float),
        'hhinc': g(f'h{ww}inc_a'), 'hhdin': g(f'h{ww}inc_a') - g(f'h{ww}exp_b').fillna(0), 'employed': emp, 'w': np.nan,
        'x_selfemp': jpo.isin([4, 5]).astype(float), 'x_regular': (jpo == 1).astype(float),
        'x_temp_daily': jpo.isin([2, 3]).astype(float), 'x_occ': pos(g(f'pw{ww}job')),
        'x_pension_enrolled': (g(f'p{ww}bc001') == 1).astype(float).where(g(f'p{ww}bc001').isin([1, 2])),
        'x_pension_amt': pos(g(f'p_{ww}_inc_ba1')).fillna(0),
        'x_pension_recv': (pos(g(f'p_{ww}_inc_ba1')).fillna(0) > 0).astype(float),
        'x_own_earn': pos(g(f'p_{ww}_inc_bb1')).fillna(0) + g(f'p_{ww}_inc_bb2').fillna(0),
        'x_fin_assets': sum(pos(d[c]).fillna(0) for c in fa),
        'x_debt': pos(g(f'h{ww}fc001')),
        'x_region': pos(g(f'hs{ww}b10')),
    })
    out.append(s)
s = pd.concat(out, ignore_index=True)
s = s[s.age.between(45, 80)]
s.to_pickle('/home/claude/work/p_nastab.pkl')
print(s.shape); print(s.groupby('svy_year').size().to_dict())
print(s.describe().T[['count', 'mean', '50%']].to_string())
