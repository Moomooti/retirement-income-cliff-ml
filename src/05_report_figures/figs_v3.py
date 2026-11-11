import numpy as np, pandas as pd, pickle, os, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from common_ml import *
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'axes.unicode_minus': False, 'font.size': 9,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#8a8984',
                     'axes.labelcolor': '#52514e', 'xtick.color': '#52514e', 'ytick.color': '#52514e', 'axes.grid': True,
                     'grid.color': '#e6e5e0', 'grid.linewidth': 0.6, 'axes.axisbelow': True, 'figure.dpi': 200, 'savefig.bbox': 'tight'})
ML, B0, B1, GR = '#2a78d6', '#eb6834', '#1baf7a', '#8a8984'
F = W + 'fig3/'; os.makedirs(F, exist_ok=True)
O = pickle.load(open(W + 'v3_out.pkl', 'rb'))
TN = {'KOWEPS_r': '복지(가처분)', 'NaSTaB_r': '재정(가처분)', 'KReIS_r': '국민노후(가처분)', 'KReIS_rn': '국민노후(필요생활비)',
      'KLIPS_r': '노동(경상·재현)', 'KHP_r': '의료(경상·이식)', 'KLoSA_r': '고령화(경상·이식)'}
MAIN = ['KOWEPS_r', 'NaSTaB_r', 'KReIS_r']
SHOW = MAIN + ['KReIS_rn', 'KLIPS_r']
FIN = '최종: LightGBM+로지스틱'
LAB = pickle.load(open(W + 'labels.pkl', 'rb'))
LAB.update({'log_dratio': '지금 가처분소득/빈곤선', 'd_log_dratio_2y': '2년 가처분소득 변화', 'log_rneed': '지금 소득/필요생활비',
            'x_need_min': '필요 최소생활비', 'x_cover_ratio': '충족률', 'x_worry': '본인 걱정', 'x_short_exp': '생활비 부족 경험',
            'x_mental_bad': '정신건강(나쁨)', 'x_hh_earn_r': '가구 근로·사업소득 비중', 'x_pub_transfer_r': '공적이전 비중',
            'x_priv_transfer_r': '사적이전 비중', 'x_fin_income_r': '금융·임대소득 비중', 'lg_x_realestate': '부동산(로그)',
            'x_realestate_r': '부동산/소득'})
pickle.dump((TN, LAB), open(W + 'v3_names.pkl', 'wb'))
Z = O['zoo']

# 1. 정답 설계 여정
v2 = pd.read_csv(W + 'label_v2.csv'); r1 = pd.read_csv(W + 'all_results.csv')
j = [('① 2년 뒤 1회 하락\n(경상, 6개 패널)', r1[r1.model == 'B0_income_only'].auc.mean(), r1[(r1.fs == 'full') & (r1.model == 'LightGBM')].auc.mean()),
     ('② 반복 부족·전원\n(상태형, 6개)', v2[v2.label == 'L2_반복부족_전체'].auc_b0.mean(), v2[v2.label == 'L2_반복부족_전체'].auc_ml.mean()),
     ('③ 2·4년 뒤 모두 하락\n(경상, 6개)', v2[v2.label == 'L1_지속하락'].auc_b0.mean(), v2[v2.label == 'L1_지속하락'].auc_ml.mean()),
     ('④ v3: 3번 중 2번\n(가처분, 3개 패널)', Z[(Z.task.isin(MAIN)) & (Z.model == 'B0 지금 소득')].auc.mean(), Z[(Z.task.isin(MAIN)) & (Z.model == FIN)].auc.mean())]
pickle.dump(j, open(W + 'v3_journey.pkl', 'wb'))
fig, ax = plt.subplots(figsize=(6.6, 2.9)); x = np.arange(len(j))
ax.bar(x - 0.18, [a for _, a, _ in j], 0.34, color=B0, label='지금 소득 하나'); ax.bar(x + 0.18, [b for _, _, b in j], 0.34, color=ML, label='ML')
for i, (_, a, b) in enumerate(j):
    ax.text(i - 0.18, a + 0.005, f'{a:.3f}', ha='center', fontsize=7); ax.text(i + 0.18, b + 0.005, f'{b:.3f}', ha='center', fontsize=7)
    ax.text(i, 0.665, f'이득 {b - a:+.3f}', ha='center', fontsize=7.5, color='#0b0b0b', fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels([n for n, _, _ in j], fontsize=7.4); ax.set_ylim(0.65, 0.95); ax.set_ylabel('시험 AUC (패널 평균)')
ax.legend(frameon=False, fontsize=7.5, loc='upper left'); ax.grid(axis='x', visible=False)
fig.savefig(F + 'g01_journey.png'); plt.close()

# 2. 포리스트
C = O['cmp']
fig, ax = plt.subplots(figsize=(6.6, 3.2)); ys = []
for i, (comp, col, lab) in enumerate([('최종−지금소득', ML, '최종 모델 − 지금 소득'), ('최종−계산기형', B1, '최종 모델 − 계산기형')]):
    off = -0.15 if i == 0 else 0.15
    for jj, k in enumerate(SHOW):
        r = C[(C.comp == comp) & (C.task == k)].iloc[0]
        ax.errorbar(r.delta, jj + off, xerr=1.96 * r.se, fmt='o', color=col, ms=5, lw=1.6, label=lab if jj == 0 else None)
    m = O['meta'][comp]; ax.errorbar(m['est'], len(SHOW) + 0.6 + off, xerr=1.96 * m['se'], fmt='D', color=col, ms=7, lw=2.2)
ax.axvline(0, color='#52514e', lw=0.8); ax.axvline(0.03, color=GR, lw=0.8, ls=':')
ax.set_yticks(list(range(len(SHOW))) + [len(SHOW) + 0.6]); ax.set_yticklabels([TN[k] for k in SHOW] + ['결합(가처분 3개, 랜덤효과)'], fontsize=8)
ax.invert_yaxis(); ax.set_xlabel('AUC 향상, 95% 신뢰구간 (DeLong)'); ax.legend(frameon=False, fontsize=7.5, loc='lower right'); ax.grid(axis='y', visible=False)
fig.savefig(F + 'g02_forest.png'); plt.close()

# 3. 모델 비교
zz = Z[Z.task.isin(MAIN)].groupby('model').auc.mean().sort_values()
fig, ax = plt.subplots(figsize=(6.4, 4.6))
cols = [B0 if m.startswith('B0') else B1 if m.startswith('B1') else ('#0d366b' if m == FIN else ML) for m in zz.index]
ax.barh(range(len(zz)), zz - 0.6, left=0.6, color=cols, height=0.62)
for i, v in enumerate(zz): ax.text(v + 0.002, i, f'{v:.3f}', va='center', fontsize=7.2, color='#52514e')
ax.set_yticks(range(len(zz))); ax.set_yticklabels(zz.index, fontsize=7.8); ax.set_xlim(0.6, zz.max() + 0.03)
ax.set_xlabel('가처분 3개 패널 평균 시험 AUC'); ax.grid(axis='y', visible=False)
fig.savefig(F + 'g03_zoo.png'); plt.close()

# 4. 질문 수 고정
FQ = O['fq']; g = FQ[FQ.set.isin(['ML 선택', '전문가 양식', '무작위']) & FQ.task.isin(MAIN)].groupby(['set', 'k']).auc.mean().unstack(0)
b0 = FQ[(FQ.set == '지금 소득') & FQ.task.isin(MAIN)].auc.mean(); allv = FQ[(FQ.set == '전체') & FQ.task.isin(MAIN)].auc.mean()
fig, ax = plt.subplots(figsize=(5.6, 2.8))
for nm, col, mk_ in [('ML 선택', ML, 'o'), ('전문가 양식', B1, 's'), ('무작위', GR, '^')]:
    ax.plot(g.index, g[nm], '-' + mk_, color=col, lw=2, ms=5, label=f'{nm}')
    ax.text(g.index[-1] + 0.4, g[nm].iloc[-1], f'{g[nm].iloc[-1]:.3f}', va='center', fontsize=7, color='#52514e')
ax.axhline(b0, color=B0, lw=1.2, ls='--'); ax.text(5, b0 + 0.003, f'지금 소득 하나 {b0:.3f}', fontsize=7, color=B0)
ax.axhline(allv, color=ML, lw=0.8, ls=':'); ax.text(5, allv + 0.003, f'전체 입력 {allv:.3f}', fontsize=7, color=ML)
ax.set_xticks([5, 12, 20]); ax.set_xlabel('질문 수 k (지금 소득 포함)'); ax.set_ylabel('가처분 3개 패널 평균 AUC')
ax.legend(frameon=False, fontsize=7, loc='center right', bbox_to_anchor=(1, 0.4)); ax.set_xlim(4, 22.5)
fig.savefig(F + 'g04_fixedq.png'); plt.close()

# 5. 학습곡선 + 반복
LC = O['lc'].groupby('frac')[['n', 'train_auc', 'test_auc']].mean().reset_index(); st = O['staged']
fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.7))
ax = axs[0]; ax.plot(LC.n, LC.train_auc, '-o', color=GR, ms=4, lw=2, label='학습 AUC'); ax.plot(LC.n, LC.test_auc, '-o', color=ML, ms=4, lw=2, label='시험 AUC')
ax.axhline(O['pool_b0'], color=B0, lw=1.2, ls='--', label='지금 소득 하나'); ax.set_xscale('log'); ax.set_xlabel('학습 행 수 (로그)'); ax.set_ylabel('AUC')
ax.legend(frameon=False, fontsize=7); ax.set_title('데이터가 늘수록 시험 성능이 오른다', fontsize=8.6, loc='left')
ax = axs[1]; ax.plot(st['iter'], st.train_auc, color=GR, lw=2, label='학습'); ax.plot(st['iter'], st.test_auc, color=ML, lw=2, label='시험')
ax.axhline(O['pool_b0'], color=B0, lw=1.2, ls='--'); ax.set_xlabel('부스팅 반복 수'); ax.legend(frameon=False, fontsize=7)
ax.set_title('반복마다 패턴을 쌓고, 시험 성능은 평탄해진다', fontsize=8.6, loc='left')
fig.tight_layout(); fig.savefig(F + 'g05_learning.png'); plt.close()

# 6. 소득 구간
bd = O['bands']; fig, ax = plt.subplots(figsize=(5.4, 2.5)); x = np.arange(len(bd))
ax.bar(x - 0.18, bd.auc_b0, 0.34, color=B0, label='지금 소득 하나'); ax.bar(x + 0.18, bd.auc_ml, 0.34, color=ML, label='ML(통합)')
for i, r in bd.iterrows():
    ax.text(i - 0.18, r.auc_b0 + 0.006, f'{r.auc_b0:.2f}', ha='center', fontsize=7); ax.text(i + 0.18, r.auc_ml + 0.006, f'{r.auc_ml:.2f}', ha='center', fontsize=7)
ax.axhline(0.5, color=GR, lw=0.8, ls=':'); ax.set_xticks(x); ax.set_xticklabels(['1.0~1.25배', '1.25~1.5배', '1.5~2배', '2배 이상'], fontsize=7.8)
ax.set_ylim(0.45, 0.9); ax.set_ylabel('구간 안 AUC'); ax.set_xlabel('지금 가처분소득 / 빈곤선'); ax.legend(frameon=False, fontsize=7.5, loc='upper left'); ax.grid(axis='x', visible=False)
fig.savefig(F + 'g06_bands.png'); plt.close()

# 7. 부분의존
fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.7))
a = O['pdp_nps']; gx = a['grid_values'][0]; av = a['average'][0]; ax = axs[0]
ax.plot(gx, av[:, 0] * 100, color=B0, lw=2, label='지금 일하지 않음'); ax.plot(gx, av[:, 1] * 100, color=ML, lw=2, label='지금 일함')
ax.axvline(0, color=GR, lw=0.8, ls=':'); ax.set_xlabel('국민연금 개시까지 (나이 − 개시연령)'); ax.set_ylabel('예측 확률 %')
ax.set_title('연금 개시 무렵 위험 구조', fontsize=8.6, loc='left'); ax.legend(frameon=False, fontsize=7)
b = O['pdp_d2']; gr = np.exp(b['grid_values'][0]); gd = b['grid_values'][1]; bv = b['average'][0]; ax = axs[1]; cm = plt.get_cmap('Blues')
for kk, jj in enumerate([1, len(gd) // 2, len(gd) - 2]):
    ax.plot(gr, bv[:, jj] * 100, color=cm(0.45 + 0.25 * kk), lw=2, label=f'최근 2년 소득 {np.exp(gd[jj]) * 100 - 100:+.0f}%')
ax.set_xlabel('지금 가처분소득 / 빈곤선'); ax.set_title('같은 소득, 다른 경로', fontsize=8.6, loc='left'); ax.legend(frameon=False, fontsize=7)
fig.tight_layout(); fig.savefig(F + 'g07_pdp.png'); plt.close()

# 8. 중요도 (과제별 상위 8)
IM = O['imp']
fig, axs = plt.subplots(2, 3, figsize=(7.0, 5.2))
for ax, k in zip(axs.flat, SHOW):
    d = IM[IM.task == k].sort_values('imp', ascending=False).head(8)[::-1]
    ax.barh(range(len(d)), d.imp, color=ML, height=0.6, xerr=d.sd, error_kw=dict(lw=0.6, ecolor=GR))
    ax.set_yticks(range(len(d))); ax.set_yticklabels([LAB.get(f, f) for f in d.feature], fontsize=6.6); ax.set_title(TN[k], fontsize=8, loc='left')
    ax.tick_params(axis='x', labelsize=6.5); ax.grid(axis='y', visible=False)
axs.flat[-1].axis('off')
fig.text(0.5, 0.0, '순열 중요도: 시험셋에서 그 변수만 섞었을 때 떨어지는 AUC', ha='center', fontsize=8, color='#52514e')
fig.tight_layout(); fig.savefig(F + 'g08_importance.png'); plt.close()

# 9. 집단별
SG = O['sub']; SG = SG[SG.task.isin(MAIN + ['KLIPS_r'])]
sm = pd.DataFrame([dict(group=gname, k=len(x), auc_b0=x.auc_b0.mean(), auc_ml=x.auc_ml.mean(), **meta_dl(x.delta, x.se)) for gname, x in SG.groupby('group', sort=False)])
pickle.dump(sm, open(W + 'v3_submeta.pkl', 'wb'))
fig, ax = plt.subplots(figsize=(5.8, 3.3))
for i, r in sm.reset_index(drop=True).iterrows():
    ax.errorbar(r.est, i, xerr=[[r.est - r.lo], [r.hi - r.est]], fmt='o', color=ML, ms=5, lw=1.6)
    ax.text(sm.hi.max() + 0.006, i, f'{r.auc_b0:.3f} → {r.auc_ml:.3f}', va='center', fontsize=7, color='#52514e')
ax.axvline(0, color='#52514e', lw=0.8); ax.set_yticks(range(len(sm))); ax.set_yticklabels(sm.group, fontsize=8); ax.invert_yaxis()
ax.set_xlabel('AUC 향상 (최종 − 지금 소득), 4개 과제 결합 95% CI'); ax.grid(axis='y', visible=False)
fig.savefig(F + 'g09_subgroup.png'); plt.close()

# 10. 보정
CA = O['cal']; fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.0), sharey=True)
cmap = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#6250d6']
for ax, kind in zip(axs, ['원 확률', '재보정']):
    for k, c in zip(SHOW, cmap):
        d = CA[(CA.task == k) & (CA.kind == kind)]; ax.plot(d.pred * 100, d.obs * 100, '-o', ms=2.5, lw=1.3, color=c, label=TN[k])
    mx = CA.obs.max() * 100 + 5; ax.plot([0, mx], [0, mx], color=GR, lw=0.8, ls=':'); ax.set_xlabel('예측 확률 %'); ax.set_title(kind, fontsize=8.6, loc='left')
axs[0].set_ylabel('실제 하락률 %'); axs[1].legend(frameon=False, fontsize=6.3)
fig.tight_layout(); fig.savefig(F + 'g10_calibration.png'); plt.close()

# 11. 이식
T = O['transfer'].astype(float); lab = [TN[k] for k in T.index]
fig, ax = plt.subplots(figsize=(5.4, 4.3)); im = ax.imshow(T.values, cmap='Blues', vmin=0.65, vmax=0.88)
for i in range(len(T)):
    for jj in range(len(T)):
        ax.text(jj, i, f'{T.values[i, jj]:.3f}', ha='center', va='center', fontsize=7, color='white' if T.values[i, jj] > 0.81 else '#0b0b0b')
ax.set_xticks(range(len(T))); ax.set_yticks(range(len(T))); ax.set_xticklabels(lab, rotation=35, ha='right', fontsize=7); ax.set_yticklabels(lab, fontsize=7)
ax.grid(False); ax.set_xlabel('평가한 과제(시험)'); ax.set_ylabel('학습한 과제'); fig.colorbar(im, fraction=0.04)
fig.savefig(F + 'g11_transfer.png'); plt.close()

# 12. 사업
BZ = O['biz']; fig, ax = plt.subplots(figsize=(6.4, 2.7)); x = np.arange(len(SHOW))
base = [BZ[(BZ.task == k) & (BZ.model == 'B0 지금 소득')].found.iloc[0] for k in SHOW]
fin = [BZ[(BZ.task == k) & (BZ.model == FIN)].found.iloc[0] for k in SHOW]
ax.bar(x - 0.18, base, 0.34, color=B0, label='기존(지금 소득 / 충족률 계산)'); ax.bar(x + 0.18, fin, 0.34, color=ML, label='최종 ML')
for i in range(len(x)):
    ax.text(i - 0.18, base[i] + 8, str(base[i]), ha='center', fontsize=7); ax.text(i + 0.18, fin[i] + 8, f'{fin[i]} ({fin[i] / base[i] - 1:+.0%})', ha='center', fontsize=7)
ax.set_xticks(x); ax.set_xticklabels([TN[k] for k in SHOW], fontsize=7.5); ax.set_ylabel('찾은 실제 하락자 수'); ax.legend(frameon=False, fontsize=7.5)
ax.set_title('위험 상위 20%로 표시된 사람 중 실제 하락자 (같은 인원 비교)', fontsize=8.6, loc='left'); ax.grid(axis='x', visible=False)
fig.savefig(F + 'g12_business.png'); plt.close()
print('figs v3 done')
