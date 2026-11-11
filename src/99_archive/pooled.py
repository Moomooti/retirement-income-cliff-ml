"""공통 입력만으로: (1) 패널 간 이전 행렬 (2) 6개 패널 통합 학습 (3) 학습곡선 (4) 라벨 셔플 검정
(5) 소득 구간 내 판별력 (6) 2차원 부분의존."""
import numpy as np, pandas as pd, pickle, warnings
from common_ml import *
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.inspection import partial_dependence
warnings.filterwarnings('ignore')
S = pd.read_pickle(W + 'analytic.pkl')
TR, TE = {}, {}
for p in PANELS:
    TR[p], TE[p] = split(S, p)
cols = COMMON
HP = dict(learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=100, l2_regularization=1.0, max_iter=400)
mk = lambda **k: HistGradientBoostingClassifier(random_state=42, **{**HP, **k})
out = {}
# (1) 이전 행렬
T = pd.DataFrame(index=PANELS, columns=PANELS, dtype=float)
for a in PANELS:
    m = mk().fit(TR[a][cols], TR[a].y)
    for b in PANELS:
        T.loc[a, b] = roc_auc_score(TE[b].y, m.predict_proba(TE[b][cols])[:, 1])
print(T.round(3)); out['transfer'] = T
# (2) 통합 학습 (패널 구분 변수 포함/미포함)
ptr = pd.concat(TR.values()); pte = pd.concat(TE.values())
for c in PANELS:
    ptr['pn_' + c] = (ptr.panel == c).astype(int); pte['pn_' + c] = (pte.panel == c).astype(int)
pc = cols + ['pn_' + c for c in PANELS]
mp = mk(max_iter=600).fit(ptr[pc], ptr.y)
pte['s_pooled'] = mp.predict_proba(pte[pc])[:, 1]
out['pooled_auc'] = {p: roc_auc_score(pte[pte.panel == p].y, pte[pte.panel == p].s_pooled) for p in PANELS}
out['pooled_auc_all'] = roc_auc_score(pte.y, pte.s_pooled)
out['pooled_b0_all'] = roc_auc_score(pte.y, -pte.log_ratio)
print('pooled', out['pooled_auc'], out['pooled_auc_all'], out['pooled_b0_all'])
pte[['panel', 'pid', 'svy_year', 'y', 'log_ratio', 's_pooled', 'age', 'employed']].to_pickle(W + 'pooled_test.pkl')
# (3) 학습곡선: 학습 데이터 비율별 시험 AUC (5회 반복)
rng = np.random.RandomState(0); LC = []
for frac in [0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 1.0]:
    for rep in range(3 if frac < 1 else 1):
        idx = rng.choice(len(ptr), int(len(ptr) * frac), replace=False)
        m = mk(max_iter=600).fit(ptr[pc].iloc[idx], ptr.y.iloc[idx])
        s = m.predict_proba(pte[pc])[:, 1]
        tr_s = m.predict_proba(ptr[pc].iloc[idx])[:, 1]
        LC.append(dict(frac=frac, n=len(idx), rep=rep, test_auc=roc_auc_score(pte.y, s),
                       train_auc=roc_auc_score(ptr.y.iloc[idx], tr_s)))
LC = pd.DataFrame(LC); print(LC.groupby('frac')[['n', 'train_auc', 'test_auc']].mean()); out['learning_curve'] = LC
# (3b) 반복 횟수(부스팅 단계)별 학습/시험 AUC
mstage = mk(max_iter=600, early_stopping=False).fit(ptr[pc], ptr.y)
st = []
for i, (a, b) in enumerate(zip(mstage.staged_predict_proba(ptr[pc]), mstage.staged_predict_proba(pte[pc]))):
    if i % 10 == 0 or i < 10:
        st.append(dict(iter=i + 1, train_auc=roc_auc_score(ptr.y, a[:, 1]), test_auc=roc_auc_score(pte.y, b[:, 1])))
out['staged'] = pd.DataFrame(st)
# (4) 라벨 셔플 검정
perm = []
for r in range(5):
    yy = ptr.y.sample(frac=1, random_state=r).values
    m = mk(max_iter=300).fit(ptr[pc], yy)
    perm.append(roc_auc_score(pte.y, m.predict_proba(pte[pc])[:, 1]))
out['perm_auc'] = perm; print('label-shuffled AUC', np.round(perm, 3))
# (5) 소득 구간별 AUC (소득만으로는 구분이 어려운 구간에서 ML의 판별력)
bands = [(1.0, 1.25), (1.25, 1.5), (1.5, 2.0), (2.0, 99)]
bb = []
for lo, hi in bands:
    d = pte[(np.exp(pte.log_ratio) >= lo) & (np.exp(pte.log_ratio) < hi)]
    bb.append(dict(band=f'{lo}~{hi if hi < 99 else ""}', n=len(d), pos=d.y.mean(),
                   auc_ml=roc_auc_score(d.y, d.s_pooled), auc_income=roc_auc_score(d.y, -d.log_ratio)))
out['bands'] = pd.DataFrame(bb); print(out['bands'])
# (6) 부분의존: 나이 × 취업 상태, 나이 × 2년 소득변화
pd1 = partial_dependence(mp, ptr[pc].sample(8000, random_state=1), features=('age', 'employed'), kind='average',
                         grid_resolution=20)
out['pd_age_emp'] = pd1
pd2 = partial_dependence(mp, ptr[pc].sample(8000, random_state=1), features=['log_ratio'], kind='average',
                         grid_resolution=30)
out['pd_ratio'] = pd2
pd3 = partial_dependence(mp, ptr[pc].sample(8000, random_state=1), features=('log_ratio', 'vol_hist'),
                         kind='average', grid_resolution=15)
out['pd_ratio_vol'] = pd3
# (7) 상태형 정답(지금 가난한 사람 포함) vs 변화형 정답: 같은 데이터·같은 모델
SA = pd.read_pickle(W + 'analytic_all.pkl'); st = []
for p in PANELS:
    a, b = split(SA, p)
    m = mk().fit(a[cols], a.y); s_ = m.predict_proba(b[cols])[:, 1]
    st.append(dict(panel=p, n=len(b), pos=b.y.mean(), auc_b0=roc_auc_score(b.y, -b.log_ratio), auc_ml=roc_auc_score(b.y, s_),
                   chg_b0=roc_auc_score(TE[p].y, -TE[p].log_ratio)))
out['state_vs_change'] = pd.DataFrame(st); print(out['state_vs_change'].round(3))
pickle.dump(out, open(W + 'pooled_out.pkl', 'wb'))
print('DONE pooled')
