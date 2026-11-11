"""국민노후보장패널(KReIS) → 공통 스키마 (코드북 v10.3 반영). 격년 조사(2005~2023), 소득은 작년 한 해.
금액 단위 천원 → ÷10 → 만원. 가구소득 = hd002b 작년한해경상소득 (다른 패널과 같은 '경상소득' 개념).
kreispl13은 kreispl05와 동일 인물·동일 값이라 중복 제외. kreishl23(2023 신규표본)은 2년 뒤 결과가 없어 제외."""
import pandas as pd, numpy as np
C = '/home/claude/raw/1_KReIS_main_csv/CSV/'
want = ['pid', 'hid', 'wave', 'age', 'sex', 'rel', 'mar', 'edu', 'num', 'area', 'pa001', 'pa002', 'pa003', 'pa005',
        'pa007', 'pd001', 'pk010', 'pk011', 'pc003', 'pc004', 'pc010', 'pc019']
p = pd.read_csv(C + 'kreispl05.csv', usecols=lambda c: c in want, low_memory=False)
for c in want:
    if c not in p: p[c] = np.nan
hcols = ['hid', 'wave', 'num', 'hc100', 'hdin', 'hd001b', 'hd002b', 'hd004b', 'hd005b', 'hd006b', 'hd007b', 'hd008b',
         'he001b', 'he002b', 'he003b', 'he004b']
h = pd.read_csv(C + 'kreishl05.csv', usecols=hcols, low_memory=False).rename(columns={'num': 'hnum'})
d = p.merge(h, on=['hid', 'wave'], how='left')
d = d[d.age.notna()]
pos = lambda s: s.where(s >= 0)
k = lambda c: d[c].where(d[c] > -9) / 10.0     # 천원 → 만원 (음수 사업소득은 유지, -9 무응답 제외)
hhs = pos(d.num).fillna(pos(d.hnum))
inc = k('hd002b')
emp = (d.pa001 == 1).astype(float).where(d.pa001 > 0)
s = pd.DataFrame({
    'panel': 'KReIS', 'pid': d.pid.astype('int64').astype(str), 'hid': d.hid.astype('int64').astype(str),
    'svy_year': d.wave, 'inc_year': d.wave - 1, 'age': d.age,
    'female': (d.sex == 2).astype(float),
    'edu3': np.select([d.edu < 4, d.edu < 5], [0, 1], 2).astype(float),
    'married': d.mar.isin([1, 11, 12]).astype(float), 'hhsize': hhs,
    'head': d.rel.isin([10, 20]).astype(float),
    'hhinc': inc, 'hhdin': k('hdin'), 'employed': emp, 'w': np.nan,
    'x_health_bad': (6 - d.pk010).where(d.pk010.between(1, 5)),      # 1 매우 좋음 ~ 5 매우 나쁨으로 뒤집음
    'x_mental_bad': (6 - d.pk011).where(d.pk011.between(1, 5)),
    'x_regular': (d.pa003 == 1).astype(float), 'x_temp_daily': d.pa003.isin([2, 3]).astype(float),
    'x_selfemp': d.pa005.isin([1, 2, 3]).astype(float),
    'x_occ': pos(d.pa007).where(d.pa001 == 1),
    'x_pension_enrolled': (d.pd001 == 1).astype(float).where(d.pd001 > 0),
    'x_pension_recv': (d.pd001 == 2).astype(float).where(d.pd001 > 0),
    'x_hh_earn': k('hd004b'),          # 가구 근로·사업소득
    'x_pub_transfer': k('hd007b'),     # 가구 공적이전소득
    'x_priv_transfer': k('hd008b'),    # 가구 사적이전소득
    'x_fin_income': k('hd005b').fillna(0) + k('hd006b').fillna(0),   # 금융+임대소득
    'x_realestate': k('he001b'), 'x_fin_assets': k('he003b'), 'x_debt': k('he004b'),
    'x_region': d.area,
})
# ---- 현장 판단 기준선(국민노후패널 전용) ----
# 필요 최소 노후생활비(월, 천원): 배우자 있으면 부부기준, 없으면 개인기준
need = pos(d.pc003).where(d.mar.isin([1, 11, 12])).fillna(pos(d.pc004)).where(lambda x: x > 0)
s['x_need_min'] = need / 10.0                                   # 월 만원
s['x_cover_ratio'] = (inc / 12.0) / (need / 10.0)               # 충족률 = 현재 월 경상소득 / 필요 최소 생활비 (기존 계산 방식)
worry = pd.Series(np.nan, index=d.index)
worry[d.pc019 == 2] = 2                                          # 노후생활비 준비 안 함
worry[(d.pc019 == 1) & (d.pc010 == 2)] = 1                      # 준비하지만 충분하지 못함
worry[(d.pc019 == 1) & (d.pc010 == 1)] = 0                      # 준비하고 충분함
worry[(d.pc019 == 1) & d.pc010.isna()] = 0.5
s['x_worry'] = worry                                             # 본인 걱정(0 충분 ~ 2 준비 안 함)
s['x_short_exp'] = (d.hc100 == 1).astype(float).where(d.hc100.isin([1, 2]))   # 생활비 부족 경험
s = s[s.age.between(45, 80)]
s.to_pickle('/home/claude/work/p_kreis.pkl')
print(s.shape); print(s.groupby('svy_year').size().to_dict())
print(s.describe().T[['count', 'mean', '50%']].to_string())
