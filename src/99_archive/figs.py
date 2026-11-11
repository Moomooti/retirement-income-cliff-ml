import numpy as np, pandas as pd, pickle, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from common_ml import *
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'axes.unicode_minus': False, 'font.size': 9,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#8a8984',
                     'axes.labelcolor': '#52514e', 'xtick.color': '#52514e', 'ytick.color': '#52514e',
                     'axes.grid': True, 'grid.color': '#e6e5e0', 'grid.linewidth': 0.6, 'axes.axisbelow': True,
                     'figure.dpi': 200, 'savefig.bbox': 'tight'})
ML, B0, B1, GR = '#2a78d6', '#eb6834', '#1baf7a', '#8a8984'
F = W + 'fig/'
import os; os.makedirs(F, exist_ok=True)
A = pickle.load(open(W + 'analysis_out.pkl', 'rb')); PO = pickle.load(open(W + 'pooled_out.pkl', 'rb'))
R = pd.read_csv(W + 'all_results.csv')
KN = {p: NAME[p] for p in PANELS}

# 1. 포리스트 플롯 ΔAUC
C = A['compare']
fig, ax = plt.subplots(figsize=(6.6, 3.3))
yl = []
for i, (comp, col, lab) in enumerate([('full_vs_B0', ML, '공통+추가 입력'), ('common_vs_B0', B1, '공통 입력만')]):
    c = C[C.comp == comp].set_index('panel').loc[PANELS]
    off = -0.15 if i == 0 else 0.15
    for j, p in enumerate(PANELS):
        r = c.loc[p]; ax.errorbar(r.delta, j + off, xerr=1.96 * r.se, fmt='o', color=col, ms=5, capsize=0, lw=1.6,
                                  label=lab if j == 0 else None)
    m = A['meta'][comp]
    ax.errorbar(m['est'], len(PANELS) + 0.6 + off, xerr=1.96 * m['se'], fmt='D', color=col, ms=7, lw=2.2)
ax.axvline(0, color='#52514e', lw=0.8); ax.axvline(0.03, color=GR, lw=0.8, ls=':')
ax.set_yticks(list(range(len(PANELS))) + [len(PANELS) + 0.6])
ax.set_yticklabels([KN[p] for p in PANELS] + ['결합(랜덤효과)'], fontsize=8.5)
ax.invert_yaxis(); ax.set_xlabel('AUC 향상 (ML − 현재 소득 하나), 95% 신뢰구간')
ax.text(0.031, -0.7, '+0.03 기준', fontsize=7, color=GR)
ax.legend(loc='lower right', frameon=False, fontsize=8); ax.grid(axis='y', visible=False)
fig.savefig(F + 'f1_forest.png'); plt.close()

# 2. 모델 동물원 (full) 평균 AUC
z = R[(R.fs == 'full') | (R.fs == 'baseline')].pivot_table(index='model', columns='panel', values='auc')[PANELS]
z['평균'] = z.mean(axis=1); z = z.sort_values('평균')
fig, ax = plt.subplots(figsize=(6.6, 6.2))
cols = [B0 if m.startswith('B0') else B1 if m.startswith('B1') else ML for m in z.index]
ax.barh(range(len(z)), z['평균'] - 0.5, left=0.5, color=cols, height=0.62)
for i, (m, v) in enumerate(z['평균'].items()):
    ax.text(v + 0.002, i, f'{v:.3f}', va='center', fontsize=7.2, color='#52514e')
lbl = {'B0_income_only': '기준: 현재 소득 하나', 'B1_calculator': '기준: 계산기형(소득·나이·취업)'}
ax.set_yticks(range(len(z))); ax.set_yticklabels([lbl.get(m, m) for m in z.index], fontsize=7.6)
ax.set_xlim(0.5, z['평균'].max() + 0.04); ax.set_xlabel('6개 패널 평균 시험 AUC'); ax.grid(axis='y', visible=False)
fig.savefig(F + 'f2_zoo.png'); plt.close()
z.to_csv(W + 'zoo_table.csv')

# 3. 학습곡선 + 부스팅 단계
LC = PO['learning_curve'].groupby('frac')[['n', 'train_auc', 'test_auc']].mean().reset_index()
st = PO['staged']
fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.7))
ax = axs[0]
ax.plot(LC.n, LC.train_auc, '-o', color=GR, ms=4, lw=2, label='학습 AUC')
ax.plot(LC.n, LC.test_auc, '-o', color=ML, ms=4, lw=2, label='시험 AUC')
ax.axhline(PO['pooled_b0_all'], color=B0, lw=1.2, ls='--', label='현재 소득 하나')
ax.set_xscale('log'); ax.set_xlabel('학습 행 수 (로그)'); ax.set_ylabel('AUC'); ax.legend(frameon=False, fontsize=7)
ax.set_title('데이터가 늘수록 시험 성능이 오른다', fontsize=9, loc='left')
ax = axs[1]
ax.plot(st['iter'], st.train_auc, color=GR, lw=2, label='학습'); ax.plot(st['iter'], st.test_auc, color=ML, lw=2, label='시험')
ax.axhline(PO['pooled_b0_all'], color=B0, lw=1.2, ls='--')
ax.set_xlabel('부스팅 반복 수'); ax.set_title('반복할수록 패턴을 쌓아 간다', fontsize=9, loc='left')
ax.legend(frameon=False, fontsize=7)
fig.tight_layout(); fig.savefig(F + 'f3_learning.png'); plt.close()

# 4. 이전 행렬
T = PO['transfer'].astype(float)
fig, ax = plt.subplots(figsize=(4.8, 3.9))
im = ax.imshow(T.values, cmap='Blues', vmin=0.6, vmax=0.86)
for i in range(6):
    for j in range(6):
        ax.text(j, i, f'{T.values[i, j]:.3f}', ha='center', va='center', fontsize=7.5,
                color='white' if T.values[i, j] > 0.78 else '#0b0b0b')
ax.set_xticks(range(6)); ax.set_yticks(range(6))
ax.set_xticklabels([KN[p] for p in PANELS], rotation=35, ha='right', fontsize=7.5)
ax.set_yticklabels([KN[p] for p in PANELS], fontsize=7.5); ax.grid(False)
ax.set_xlabel('평가한 패널(시험)'); ax.set_ylabel('학습한 패널')
fig.colorbar(im, fraction=0.04); fig.savefig(F + 'f4_transfer.png'); plt.close()

# 5. 소득 구간별
bd = PO['bands']
fig, ax = plt.subplots(figsize=(5.6, 2.6)); x = np.arange(len(bd))
ax.bar(x - 0.18, bd.auc_income, 0.34, color=B0, label='현재 소득 하나')
ax.bar(x + 0.18, bd.auc_ml, 0.34, color=ML, label='ML(공통 입력)')
for i, r in bd.iterrows():
    ax.text(i - 0.18, r.auc_income + 0.008, f'{r.auc_income:.2f}', ha='center', fontsize=7)
    ax.text(i + 0.18, r.auc_ml + 0.008, f'{r.auc_ml:.2f}', ha='center', fontsize=7)
ax.axhline(0.5, color=GR, lw=0.8, ls=':')
ax.set_xticks(x); ax.set_xticklabels([f'빈곤선의 {b.replace("~", "~")}배' if '99' not in b else '' for b in bd.band], fontsize=7.8)
ax.set_xticklabels(['1.0~1.25배', '1.25~1.5배', '1.5~2배', '2배 이상'], fontsize=7.8)
ax.set_ylim(0.45, 0.85); ax.set_ylabel('구간 안 AUC'); ax.legend(frameon=False, fontsize=7.5, loc='upper left')
ax.set_xlabel('t 시점 소득 / 빈곤선'); ax.grid(axis='x', visible=False)
fig.savefig(F + 'f5_bands.png'); plt.close()

# 6. 부분의존 (확률, brute)
PD = pickle.load(open(W + 'pdp.pkl', 'rb'))
fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.7))
a = PD['agenps_emp']; gx = a['grid_values'][0]; av = a['average'][0]
ax = axs[0]
ax.plot(gx, av[:, 0] * 100, color=B0, lw=2, label='지금 일하지 않음'); ax.plot(gx, av[:, 1] * 100, color=ML, lw=2, label='지금 일함')
ax.axvline(0, color=GR, lw=0.8, ls=':'); ax.text(0.3, av.min() * 100, '연금 개시', fontsize=7, color=GR)
ax.set_xlabel('국민연금 수급 개시까지 (나이 − 개시연령, 년)'); ax.set_ylabel('예측 하락 확률 %')
ax.set_title('연금 개시가 다가오면 ‘일함’의 보호가 줄어든다', fontsize=8.6, loc='left'); ax.legend(frameon=False, fontsize=7)
b = PD['ratio_d2']; gr = np.exp(b['grid_values'][0]); gd = b['grid_values'][1]; bv = b['average'][0]
ax = axs[1]; cm = plt.get_cmap('Blues')
for k, j in enumerate([1, 6, 13]):
    ax.plot(gr, bv[:, j] * 100, color=cm(0.45 + 0.25 * k), lw=2, label=f'최근 2년 소득 {np.exp(gd[j]) * 100 - 100:+.0f}%')
ax.set_xlabel('t 시점 소득 / 빈곤선'); ax.set_xlim(1, 4.2)
ax.set_title('같은 소득이라도 최근에 오른 소득은 다시 떨어지기 쉽다', fontsize=8.6, loc='left'); ax.legend(frameon=False, fontsize=7)
fig.tight_layout(); fig.savefig(F + 'f6_pdp.png'); plt.close()

# 7. 중요도 (패널별 상위)
IM = A['imp']
LAB = {'log_ratio': '현재 소득/빈곤선', 'min_ratio_hist': '최근 4년 최저 소득', 'vol_hist': '소득 변동성',
       'd_log_ratio_2y': '2년 소득 변화', 'd_log_ratio_4y': '4년 소득 변화', 'employed': '현재 취업',
       'age': '나이', 'age_to_60': '60세까지 거리', 'age_to_nps': '연금 개시까지 거리', 'hhsize': '가구원 수',
       'married': '배우자', 'edu3': '학력', 'female': '여성', 'ever_below_hist': '과거 빈곤 경험',
       'lost_job_2y': '2년 내 실직', 'hh_change_2y': '가구원 변화', 'employed_l2': '2년 전 취업',
       'x_earn_share': '본인 근로소득 비중', 'd_log_ratio_1y': '1년 소득 변화', 'employed_l1': '1년 전 취업',
       'x_regular': '상용직', 'x_selfemp': '자영업', 'x_temp_daily': '임시·일용직', 'x_occ': '직종',
       'x_pension_recv': '공적연금 수급', 'x_pension_enrolled': '공적연금 가입', 'x_health_bad': '주관적 건강(나쁨)',
       'x_chronic': '만성질환', 'x_fin_assets_r': '금융자산/소득', 'x_debt_r': '부채/소득', 'lg_x_fin_assets': '금융자산(로그)',
       'lg_x_debt': '부채(로그)', 'x_owner': '자가 거주', 'x_region': '지역', 'x_own_earn_l2': '2년 전 본인 근로소득',
       'x_retired': '은퇴 응답', 'x_pension_amt_r': '연금액/소득', 'x_net_assets_r': '순자산/소득',
       'lg_x_net_assets': '순자산(로그)', 'x_health_bad_l2': '2년 전 건강', 'x_health_bad_d2': '건강 변화',
       'x_house_value_r': '주택가격/소득', 'lg_x_house_value': '주택가격(로그)', 'x_adl': 'ADL 제한', 'x_iadl': 'IADL 제한',
       'x_transfer_from_children_r': '자녀 이전소득/소득', 'x_realestate_r': '부동산/소득', 'x_pension_type': '연금 가입형태',
       'x_private_pension': '개인연금', 'x_retire_pension': '퇴직연금', 'x_src_hd004_r': '가구소득원 hd004 비중',
       'x_src_hd007_r': '가구소득원 hd007 비중', 'x_src_hd008_r': '가구소득원 hd008 비중',
       'x_ast_he001_r': '자산블록 he001/소득', 'x_ast_he002_r': '자산블록 he002/소득', 'x_ast_he003_r': '자산블록 he003/소득',
       'x_ast_he004_r': '자산블록 he004/소득', 'lg_x_ast_he001': '자산블록 he001(로그)', 'lg_x_ast_he002': '자산블록 he002(로그)',
       'x_disability': '장애', 'x_mental_bad': '정신건강(나쁨)', 'x_hh_earn_r': '가구 근로·사업소득 비중',
       'x_pub_transfer_r': '공적이전소득 비중', 'x_priv_transfer_r': '사적이전소득 비중', 'x_fin_income_r': '금융·임대소득 비중',
       'lg_x_realestate': '부동산(로그)', 'x_cover_ratio': '충족률(소득/필요생활비)', 'x_need_min': '필요 최소 생활비', 'x_worry': '본인 걱정', 'x_short_exp': '생활비 부족 경험', 'x_health_ins': '건강보험 유형'}
pickle.dump(LAB, open(W + 'labels.pkl', 'wb'))
IM['rank'] = IM.groupby('panel').imp.rank(ascending=False)
agg = IM.groupby('feature').agg(mean_imp=('imp', 'mean'), n=('panel', 'size'), top5=('rank', lambda r: (r <= 5).sum()))
agg = agg.sort_values('mean_imp', ascending=False).head(14)[::-1]
fig, ax = plt.subplots(figsize=(6.2, 3.8))
ax.barh(range(len(agg)), agg.mean_imp, color=ML, height=0.6)
ax.set_yticks(range(len(agg))); ax.set_yticklabels([LAB.get(f, f) for f in agg.index], fontsize=8)
for i, (f, r) in enumerate(agg.iterrows()):
    ax.text(r.mean_imp + 0.0005, i, f'{int(r.top5)}/{int(r.n)}개 패널 상위5', va='center', fontsize=6.8, color='#52514e')
ax.set_xlabel('순열 중요도: 섞었을 때 떨어지는 시험 AUC (패널 평균)'); ax.grid(axis='y', visible=False)
fig.savefig(F + 'f7_importance.png'); plt.close()

# 8. 위험 10분위
D = A['deciles']
fig, axs = plt.subplots(2, 3, figsize=(6.8, 3.9), sharey=True)
for ax, p in zip(axs.flat, PANELS):
    for lab, col in [('현재소득', B0), ('ML', ML)]:
        d = D[(D.panel == p) & (D.model == lab)]
        ax.plot(d.decile, d.rate * 100, '-o', color=col, ms=3, lw=1.8, label='현재 소득 하나' if lab == '현재소득' else 'ML')
    ax.set_title(KN[p], fontsize=8.5, loc='left'); ax.set_xticks([1, 5, 10])
for ax in axs[:, 0]: ax.set_ylabel('실제 하락률 %')
for ax in axs[1]: ax.set_xlabel('위험 10분위')
axs[0, 0].legend(frameon=False, fontsize=7)
fig.tight_layout(); fig.savefig(F + 'f8_deciles.png'); plt.close()

# 9. 보정
CA = A['cal']
fig, ax = plt.subplots(figsize=(3.4, 3.1))
cmap = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#6250d6']
for p, c in zip(PANELS, cmap):
    d = CA[CA.panel == p]; ax.plot(d.pred * 100, d.obs * 100, '-o', ms=2.5, lw=1.3, color=c, label=KN[p])
mx = max(CA.pred.max(), CA.obs.max()) * 100
ax.plot([0, mx], [0, mx], color=GR, lw=0.8, ls=':'); ax.set_xlabel('예측 확률 %'); ax.set_ylabel('실제 하락률 %')
ax.legend(frameon=False, fontsize=6.3)
fig.savefig(F + 'f9_calibration.png'); plt.close()
print('figs done')

# ---------- 검증 보강 그림 ----------
E = pickle.load(open(W + 'extra_out.pkl', 'rb'))
FQ = E['fixedq']
g = FQ[FQ.set.isin(['ML 선택', '전문가 양식', '무작위'])].groupby(['set', 'k']).auc.mean().unstack(0)
b0 = FQ[FQ.set == '지금 소득'].auc.mean(); allv = FQ[FQ.set == '전체'].auc.mean()
fig, ax = plt.subplots(figsize=(5.6, 2.8))
for nm, col, mk_ in [('ML 선택', ML, 'o'), ('전문가 양식', B1, 's'), ('무작위', GR, '^')]:
    ax.plot(g.index, g[nm], '-' + mk_, color=col, lw=2, ms=5, label=f'{nm} k개')
    ax.text(g.index[-1] + 0.4, g[nm].iloc[-1], f'{g[nm].iloc[-1]:.3f}', va='center', fontsize=7, color='#52514e')
ax.axhline(b0, color=B0, lw=1.2, ls='--'); ax.text(5, b0 + 0.003, f'지금 소득 하나 {b0:.3f}', fontsize=7, color=B0)
ax.axhline(allv, color=ML, lw=0.8, ls=':'); ax.text(5, allv + 0.003, f'전체 입력 {allv:.3f}', fontsize=7, color=ML)
ax.set_xticks([5, 12, 20]); ax.set_xlabel('질문 수 k (지금 소득 포함)'); ax.set_ylabel('6개 패널 평균 시험 AUC')
ax.legend(frameon=False, fontsize=7, loc='center right', bbox_to_anchor=(1, 0.38)); ax.set_xlim(4, 22.5)
fig.savefig(F + 'f10_fixedq.png'); plt.close()

SGm = E['subgroup_meta']
fig, ax = plt.subplots(figsize=(5.6, 3.0))
for i, r in SGm.reset_index(drop=True).iterrows():
    ax.errorbar(r.est, i, xerr=[[r.est - r.lo], [r.hi - r.est]], fmt='o', color=ML, ms=5, lw=1.6)
    ax.text(max(SGm.hi) + 0.005, i, f'{r.auc_b0:.3f} → {r.auc_ml:.3f}', va='center', fontsize=7, color='#52514e')
ax.axvline(0, color='#52514e', lw=0.8)
ax.set_yticks(range(len(SGm))); ax.set_yticklabels(SGm.group, fontsize=8); ax.invert_yaxis()
ax.set_xlabel('AUC 향상 (ML − 지금 소득), 6개 패널 결합 95% CI'); ax.grid(axis='y', visible=False)
fig.savefig(F + 'f11_subgroup.png'); plt.close()
print('extra figs done')
