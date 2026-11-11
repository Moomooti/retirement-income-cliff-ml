"""EDA – 집계만 출력 (개인 값 없음, 칸 인원 30명 미만은 표시 안 함)"""
import numpy as np, pandas as pd, pickle, json, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
W = '/home/claude/work/'; OUT = '/tmp/claude-0/-home-claude/e5872982-71a4-5f1c-953f-30befae32eac/scratchpad/doc/'
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'axes.unicode_minus': False, 'font.size': 10})
GOLD, BLUE, INK, MUTED, GRID = '#9a6b12', '#2f6db5', '#2b2b2b', '#6b6b6b', '#e6e6e6'
SF = pickle.load(open(W + 's_features.pkl', 'rb'))['SF']; key = ['panel', 'pid', 'svy_year']
tr, te, _ = pickle.load(open(W + 'v3_data_KOWEPS_r.pkl', 'rb'))
D = pd.concat([tr.assign(set='학습'), te.assign(set='시험')], ignore_index=True).merge(SF, on=key, how='left')
R = {}
def rate(g, col, order=None):
    t = D.groupby(g, observed=True).y.agg(['size', 'mean']).rename(columns={'size': 'n', 'mean': 'rate'})
    t = t[t.n >= 30]; t['rate'] = (t.rate * 100).round(1)
    return t.reindex(order).dropna() if order else t
R['n_rows'] = len(D); R['n_people'] = int(D.pid.nunique()); R['base'] = round(D.y.mean() * 100, 1)
R['years'] = [int(D.svy_year.min()), int(D.svy_year.max())]
r = np.exp(D.s_log_r)
D['rb'] = pd.cut(r, [1, 1.25, 1.5, 2, 3, np.inf], right=False, labels=['1.0~1.25배', '1.25~1.5배', '1.5~2배', '2~3배', '3배 이상'])
D['ab'] = pd.cut(D.age, [50, 55, 60, 65, 70], right=False, labels=['50~54세', '55~59세', '60~64세', '65~69세'])
D['wk'] = np.select([D.s_lost == 1, D.employed == 1, D.employed == 0], ['최근 2년 내 일 그만둠', '지금 일함', '일 안 함(2년 전에도)'], '모름')
ch = np.exp(D.s_d2) - 1
D['cb'] = pd.cut(ch, [-np.inf, -0.3, -0.1, 0.1, np.inf], labels=['30% 넘게 줄어듦', '10~30% 줄어듦', '비슷함(±10%)', '10% 넘게 늘어남'])
D['hb'] = np.where(D.hhsize == 1, '1인 가구', '2인 이상')
D['pb'] = np.where(D.x_pension_recv == 1, '공적연금 받음', '공적연금 안 받음')
tabs = {'소득 구간': rate('rb', None, None), '나이': rate('ab', None, None), '일': rate('wk', None, ['지금 일함', '일 안 함(2년 전에도)', '최근 2년 내 일 그만둠']),
        '2년 소득 변화': rate('cb', None, None), '가구': rate('hb', None, ['2인 이상', '1인 가구']), '연금': rate('pb', None, ['공적연금 받음', '공적연금 안 받음']),
        '연도': rate('svy_year', None, None)}
R['tabs'] = {k: [[str(i), int(v.n), float(v.rate)] for i, v in t.iterrows()] for k, t in tabs.items()}
# 결측률 (화면 문항에 해당하는 변수)
miss = {'1년 전 소득': D.rr_l1.isna().mean(), '2년 전 소득': D.rr_l2.isna().mean(), '금융자산': D.x_fin_assets.isna().mean(), '부채': D.x_debt.isna().mean(),
        '부동산': D.s_lg_real.isna().mean(), '건강': D.x_health_bad.isna().mean(), '일의 형태': D.x_regular.isna().mean()}
R['missing'] = {k: round(float(v) * 100, 1) for k, v in miss.items()}
# 소득 비율 분포 (히스토그램용 구간 개수)
edges = np.arange(1, 4.26, 0.25); h, _ = np.histogram(r.clip(upper=4.1), edges); R['r_hist'] = dict(edges=edges.tolist(), counts=h.tolist())
R['r_median'] = round(float(np.median(r)), 2)
json.dump(R, open(OUT + 'eda.json', 'w'), ensure_ascii=False, indent=1)

def style(ax, title):
    ax.set_title(title, loc='left', fontsize=11.5, color=INK, pad=10, fontweight='bold')
    for s in ['top', 'right', 'left']: ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color('#bdbdbd'); ax.tick_params(colors=MUTED, length=0); ax.grid(axis='x', color=GRID, lw=.8); ax.set_axisbelow(True)
def hbar(name, title, tab, note):
    t = tab.iloc[::-1]; fig, ax = plt.subplots(figsize=(6.4, .48 * len(t) + 1.25), dpi=200)
    ax.barh(range(len(t)), t.rate, color=GOLD, height=.58)
    ax.axvline(R['base'], color=MUTED, lw=1, ls=(0, (3, 3)))
    ax.text(R['base'], -0.75, f" 전체 평균 {R['base']}%", color=MUTED, fontsize=8.5, va='center')
    ax.set_ylim(-1.1, len(t) - .4)
    for i, (lab, v) in enumerate(t.iterrows()): ax.text(v.rate + .3, i, f"{v.rate:.1f}%  (n={int(v.n):,})", va='center', fontsize=8.8, color=INK)
    ax.set_yticks(range(len(t))); ax.set_yticklabels(t.index, color=INK); ax.set_xlim(0, max(t.rate.max() * 1.45, R['base'] * 1.6))
    ax.set_xlabel('2년 뒤 반복 하락 비율(%)', color=MUTED, fontsize=9); style(ax, title)
    fig.text(.01, .01, note, fontsize=7.5, color=MUTED); fig.tight_layout(rect=(0, .04, 1, 1)); fig.savefig(OUT + name, facecolor='white'); plt.close(fig)
NOTE = '한국복지패널 50~69세 · 지금 기준선 위 · 학습+시험 합계, 30명 미만 칸은 표시 안 함'
hbar('eda_income.png', '지금 소득(기준선 대비)이 낮을수록 2년 뒤 하락이 많다', tabs['소득 구간'], NOTE)
hbar('eda_work.png', '일하지 않으면 하락 비율이 높다 (지금 일하는 사람의 약 1.6배)', tabs['일'], NOTE)
hbar('eda_change.png', '반짝 늘어난 소득도 다시 내려가기 쉽다 (2년 소득 변화별)', tabs['2년 소득 변화'], NOTE)
hbar('eda_age.png', '나이가 많을수록 하락 비율이 높다 (65~69세는 50~54세의 4배)', tabs['나이'], NOTE)
hbar('eda_hh_pension.png', '1인 가구는 하락 비율이 약 2.7배 (가구·연금별)', pd.concat([tabs['가구'], tabs['연금']]), NOTE)
# 소득 비율 분포
fig, ax = plt.subplots(figsize=(6.4, 2.9), dpi=200); e = np.array(R['r_hist']['edges'])
ax.bar(e[:-1], h, width=.23, align='edge', color=GOLD); ax.axvline(R['r_median'], color=MUTED, lw=1, ls=(0, (3, 3)))
ax.text(R['r_median'], h.max() * .95, f" 중앙값 {R['r_median']}배", color=MUTED, fontsize=8.5)
ax.set_xlabel('지금 소득 ÷ 생활 기준선 (맨 오른쪽 칸 = 4배 이상)', color=MUTED, fontsize=9); ax.set_ylabel('행 수', color=MUTED, fontsize=9)
style(ax, '지금 소득 분포: 대부분 기준선의 1~3배'); ax.grid(axis='y', color=GRID); ax.grid(axis='x', visible=False)
fig.tight_layout(); fig.savefig(OUT + 'eda_rdist.png', facecolor='white'); plt.close(fig)
# 연도별
t = tabs['연도']; fig, ax = plt.subplots(figsize=(6.4, 2.8), dpi=200)
yy = t.index.astype(int)
for seg in [yy < 2018, yy > 2018]: ax.plot(yy[seg], t.rate[seg], color=GOLD, lw=2, marker='o', ms=4)
ax.text(2018, 2.2, '2017~2019 기준 차수는\n학습·시험 사이 간격(결과가 겹치지 않게 비움)', ha='center', fontsize=7.5, color=MUTED)
te_years = sorted(te.svy_year.unique()); ax.axvspan(min(te_years) - .5, max(te_years) + .5, color='#f3ead6', zorder=0)
ax.text(np.mean(te_years), t.rate.max() * .98, '봉인 시험', ha='center', fontsize=8.5, color=GOLD)
ax.set_ylim(0, t.rate.max() * 1.25); ax.set_ylabel('하락 비율(%)', color=MUTED, fontsize=9)
style(ax, '조사연도별 2년 뒤 반복 하락 비율'); ax.grid(axis='y', color=GRID); ax.grid(axis='x', visible=False)
fig.tight_layout(); fig.savefig(OUT + 'eda_year.png', facecolor='white'); plt.close(fig)
# 결측률
m = pd.Series(R['missing']).sort_values(); fig, ax = plt.subplots(figsize=(6.4, 2.9), dpi=200)
ax.barh(range(len(m)), m.values, color=BLUE, height=.55)
for i, v in enumerate(m.values): ax.text(v + .5, i, f'{v:.1f}%', va='center', fontsize=8.8, color=INK)
ax.set_yticks(range(len(m))); ax.set_yticklabels(m.index, color=INK); ax.set_xlim(0, max(m.max() * 1.3, 10)); ax.set_xlabel('비어 있는 비율(%)', color=MUTED, fontsize=9)
style(ax, '화면 문항에 해당하는 변수의 결측률'); fig.tight_layout(); fig.savefig(OUT + 'eda_missing.png', facecolor='white'); plt.close(fig)
print(json.dumps({k: v for k, v in R.items() if k != 'r_hist'}, ensure_ascii=False, indent=0)[:2500])
