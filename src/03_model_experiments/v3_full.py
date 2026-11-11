"""정답 v3 전체 분석: 모델 비교 · DeLong/메타 · 사람 단위 부트스트랩 · 질문 수 고정 · 학습곡선/셔플 · 중요도/부분의존
· 집단별/처음 보는 사람 · 보정/이식 · 사업 지표."""
import numpy as np, pandas as pd, pickle, warnings, time, sys
from scipy.stats import rankdata
from common_ml import *
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, SplineTransformer, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (RandomForestClassifier, ExtraTreesClassifier, AdaBoostClassifier, GradientBoostingClassifier,
                              HistGradientBoostingClassifier)
from sklearn.inspection import permutation_importance, partial_dependence
import lightgbm as lgb, xgboost as xgb
from catboost import CatBoostClassifier
warnings.filterwarnings('ignore')
RS = 42
TASKS = [('KOWEPS', 'r', 'log_dratio', 'main'), ('NaSTaB', 'r', 'log_dratio', 'main'), ('KReIS', 'r', 'log_dratio', 'main'),
         ('KReIS', 'rn', 'log_rneed', 'need'), ('KLIPS', 'r', 'log_dratio', 'repl'), ('KHP', 'r', 'log_dratio', 'transfer'),
         ('KLoSA', 'r', 'log_dratio', 'transfer')]
TK = lambda t: f'{t[0]}_{t[1]}'
out = {'zoo': [], 'cmp': [], 'boot': [], 'fq': [], 'imp': [], 'sub': [], 'new': [], 'cal': [], 'calsum': [], 'biz': []}
DATA, PRED, MODELS = {}, {}, {}


def winsor(X, Xt):
    X, Xt = X.copy(), Xt.copy()
    for c in X.columns:
        if c in CATEG or X[c].nunique() <= 3: continue
        lo, hi = X[c].quantile([0.005, 0.995]); X[c] = X[c].clip(lo, hi); Xt[c] = Xt[c].clip(lo, hi)
    return X, Xt


def prep(cols, spline=False):
    num = [c for c in cols if c not in CATEG]; cat = [c for c in cols if c in CATEG]
    steps = [SimpleImputer(strategy='median', add_indicator=True), StandardScaler()]
    if spline: steps.append(SplineTransformer(n_knots=5, degree=3, extrapolation='linear'))
    t = [('n', make_pipeline(*steps), num)]
    if cat: t.append(('c', make_pipeline(SimpleImputer(strategy='constant', fill_value=-1),
                                         OneHotEncoder(handle_unknown='infrequent_if_exist', min_frequency=50, sparse_output=False)), cat))
    return ColumnTransformer(t)


def tune(kind, X, y, it, iv):
    grids = {'lgb': [dict(num_leaves=n, min_child_samples=m) for n in (15, 31) for m in (40, 150)],
             'xgb': [dict(max_depth=d, min_child_weight=m) for d in (3, 5) for m in (5, 30)],
             'cat': [dict(depth=d, l2_leaf_reg=l) for d in (4, 6) for l in (3, 10)],
             'hgb': [dict(max_leaf_nodes=n, min_samples_leaf=m) for n in (15, 31) for m in (40, 150)]}
    best = None
    for g in grids[kind]:
        if kind == 'lgb':
            m = lgb.LGBMClassifier(n_estimators=3000, learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                                   reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=RS, **g)
            m.fit(X[it], y[it], eval_set=[(X[iv], y[iv])], eval_metric='auc', callbacks=[lgb.early_stopping(100, verbose=False)]); n = m.best_iteration_
        elif kind == 'xgb':
            m = xgb.XGBClassifier(n_estimators=3000, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, tree_method='hist',
                                  eval_metric='auc', early_stopping_rounds=100, n_jobs=2, random_state=RS, **g)
            m.fit(X[it], y[it], eval_set=[(X[iv], y[iv])], verbose=False); n = m.best_iteration + 1
        elif kind == 'cat':
            m = CatBoostClassifier(iterations=3000, learning_rate=0.05, eval_metric='AUC', od_type='Iter', od_wait=100,
                                   random_seed=RS, verbose=False, thread_count=2, **g)
            m.fit(X[it], y[it], eval_set=(X[iv], y[iv]), use_best_model=True); n = m.get_best_iteration() + 1
        else:
            m = HistGradientBoostingClassifier(learning_rate=0.05, max_iter=1500, early_stopping=False, random_state=RS, **g)
            m.fit(X[it], y[it])
            aucs = [roc_auc_score(y[iv], s[:, 1]) for s in m.staged_predict_proba(X[iv])]; n = int(np.argmax(aucs)) + 1
        a = roc_auc_score(y[iv], (m.predict_proba(X[iv])[:, 1] if kind != 'hgb' else list(m.staged_predict_proba(X[iv]))[n - 1][:, 1]))
        if best is None or a > best[0]: best = (a, g, n)
    a, g, n = best; n = max(50, int(n * 1.1))
    if kind == 'lgb': m = lgb.LGBMClassifier(n_estimators=n, learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0, verbose=-1, n_jobs=2, random_state=RS, **g)
    elif kind == 'xgb': m = xgb.XGBClassifier(n_estimators=n, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, tree_method='hist', n_jobs=2, random_state=RS, **g)
    elif kind == 'cat': m = CatBoostClassifier(iterations=n, learning_rate=0.05, random_seed=RS, verbose=False, thread_count=2, **g)
    else: m = HistGradientBoostingClassifier(learning_rate=0.05, max_iter=n, early_stopping=False, random_state=RS, **g)
    return m.fit(X, y), dict(inner=a, params=g, iters=n)


# =============== 1. 과제별 모델 비교 ===============
for t in TASKS:
    p, base, b0col, role = t; k = TK(t); t0 = time.time()
    tr, te, cols = pickle.load(open(W + f'v3_data_{p}_{base}.pkl', 'rb'))
    tr, te = tr.reset_index(drop=True), te.reset_index(drop=True)
    X, Xt = winsor(tr[cols].astype(float), te[cols].astype(float)); y, yt = tr.y.values, te.y.values
    vy = sorted(tr.svy_year.unique())[-2:]; iv = tr.svy_year.isin(vy).values; it = (tr.svy_year <= min(vy) - 4).values
    DATA[k] = dict(tr=tr, te=te, cols=cols, X=X, Xt=Xt, it=it, iv=iv, role=role, b0col=b0col)
    S = {'B0 지금 소득': -te[b0col].values}
    calc = make_pipeline(SimpleImputer(), StandardScaler(), LogisticRegression()).fit(tr[[b0col, 'age', 'employed']], y)
    S['B1 계산기형'] = calc.predict_proba(te[[b0col, 'age', 'employed']])[:, 1]
    zoo = {
        'LR_L2': make_pipeline(prep(cols), LogisticRegression(C=1.0, max_iter=3000)),
        'LR_L1': make_pipeline(prep(cols), LogisticRegression(penalty='l1', C=0.1, solver='liblinear')),
        'GAM_Spline_LR': make_pipeline(prep(cols, True), LogisticRegression(C=0.3, max_iter=3000)),
        'LDA': make_pipeline(prep(cols), LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')),
        'GaussianNB': make_pipeline(prep(cols), GaussianNB()),
        'KNN_k101': make_pipeline(prep(cols), KNeighborsClassifier(n_neighbors=101, weights='distance', n_jobs=2)),
        'DecisionTree': make_pipeline(prep(cols), DecisionTreeClassifier(max_depth=6, min_samples_leaf=50, random_state=RS)),
        'RandomForest': make_pipeline(prep(cols), RandomForestClassifier(n_estimators=400, min_samples_leaf=20, n_jobs=2, random_state=RS)),
        'ExtraTrees': make_pipeline(prep(cols), ExtraTreesClassifier(n_estimators=400, min_samples_leaf=20, max_features=0.5, n_jobs=2, random_state=RS)),
        'AdaBoost': make_pipeline(prep(cols), AdaBoostClassifier(n_estimators=300, learning_rate=0.5, random_state=RS)),
        'GradientBoosting': make_pipeline(prep(cols), GradientBoostingClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=RS)),
    }
    for nm, m in zoo.items():
        m.fit(X, y); S[nm] = m.predict_proba(Xt)[:, 1]
        if nm == 'LR_L2': MODELS[(k, 'LR')] = m
    for nm, kind in [('HistGB', 'hgb'), ('XGBoost', 'xgb'), ('LightGBM', 'lgb'), ('CatBoost', 'cat')]:
        hc = [c for c in cols if X.loc[it, c].nunique() > 1] if kind == 'hgb' else cols   # 학습 앞부분에서 비어 있는 열 제외(HGB 분할 오류 방지)
        m, info = tune(kind, X[hc], y, it, iv); S[nm] = m.predict_proba(Xt[hc])[:, 1]; MODELS[(k, nm)] = m
        out.setdefault('tune', []).append(dict(task=k, model=nm, **info))
    S['최종: LightGBM+로지스틱'] = rankdata(S['LightGBM']) + rankdata(S['LR_L2'])
    for nm, s in S.items():
        out['zoo'].append(dict(task=k, panel=p, role=role, model=nm, auc=roc_auc_score(yt, s)))
    PRED[k] = pd.DataFrame(S); PRED[k]['y'] = yt; PRED[k]['pid'] = te.pid.values; PRED[k]['hid'] = te.hid.values
    for nm, (a, b) in {'최종−지금소득': ('최종: LightGBM+로지스틱', 'B0 지금 소득'), 'LightGBM−지금소득': ('LightGBM', 'B0 지금 소득'),
                       '로지스틱−지금소득': ('LR_L2', 'B0 지금 소득'), 'LightGBM−로지스틱': ('LightGBM', 'LR_L2'),
                       '최종−계산기형': ('최종: LightGBM+로지스틱', 'B1 계산기형')}.items():
        A_, B_, d, se, pv_, _ = delong_diff(yt, S[a], S[b])
        out['cmp'].append(dict(task=k, panel=p, role=role, comp=nm, auc_a=A_, auc_b=B_, delta=d, se=se, p=pv_))
    # 사업 지표: 같은 인원(상위 20%) 상담 시 만나는 하락자
    k20 = int(len(yt) * 0.2)
    for nm in ['B0 지금 소득', 'B1 계산기형', 'LR_L2', 'LightGBM', '최종: LightGBM+로지스틱']:
        out['biz'].append(dict(task=k, model=nm, k20=k20, found=int(yt[np.argsort(-S[nm])[:k20]].sum()), falls=int(yt.sum()), n=len(yt)))
    print(k, 'done', round(time.time() - t0), 's', {n: round(roc_auc_score(yt, s), 3) for n, s in S.items() if n in ('B0 지금 소득', 'LR_L2', 'LightGBM', '최종: LightGBM+로지스틱')}, flush=True)
    pickle.dump(dict(out=out, PRED=PRED), open(W + 'v3_partial.pkl', 'wb'))

MAIN = [TK(t) for t in TASKS if t[3] == 'main']
out['meta'] = {c: meta_dl(g.delta, g.se) for c, g in pd.DataFrame(out['cmp']).query('task in @MAIN').groupby('comp')}
print({c: round(v['est'], 4) for c, v in out['meta'].items()}, flush=True)

# =============== 2. 사람 단위 부트스트랩 ===============
rng = np.random.RandomState(7)
for k in MAIN + ['KReIS_rn', 'KLIPS_r']:
    d = PRED[k]; pids = d.pid.unique(); idx = d.groupby('pid').indices
    for nm, (a, b) in {'최종−지금소득': ('최종: LightGBM+로지스틱', 'B0 지금 소득'), '최종−계산기형': ('최종: LightGBM+로지스틱', 'B1 계산기형'),
                       'LightGBM−로지스틱': ('LightGBM', 'LR_L2')}.items():
        ds = []
        for r in range(300):
            ii = np.concatenate([idx[q] for q in rng.choice(pids, len(pids))]); yy = d.y.values[ii]
            ds.append(roc_auc_score(yy, d[a].values[ii]) - roc_auc_score(yy, d[b].values[ii]))
        out['boot'].append(dict(task=k, comp=nm, delta=roc_auc_score(d.y, d[a]) - roc_auc_score(d.y, d[b]), se=np.std(ds),
                                lo=np.percentile(ds, 2.5), hi=np.percentile(ds, 97.5), n_persons=len(pids)))
B = pd.DataFrame(out['boot']); out['boot_meta'] = {c: meta_dl(g.delta, g.se) for c, g in B[B.task.isin(MAIN)].groupby('comp')}
print('boot', {c: round(v['est'], 4) for c, v in out['boot_meta'].items()}, flush=True)

# =============== 3. 질문 수 고정 ===============
EXPERT = ['age', 'employed', 'married', 'hhsize', 'x_pension_recv', 'x_pension_enrolled', 'x_owner', 'lg_x_fin_assets',
          'lg_x_debt', 'lg_x_realestate', 'x_health_bad', 'x_chronic', 'edu3', 'female', 'x_regular', 'x_selfemp',
          'x_private_pension', 'x_occ', 'x_region', 'x_need_min', 'x_temp_daily', 'employed_l2', 'd_log_ratio_2y']
fast = lambda: lgb.LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=15, min_child_samples=80, subsample=0.8,
                                  subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=2, random_state=RS)
for k in MAIN + ['KLIPS_r']:
    D = DATA[k]; X, Xt, y, yt, it, iv, b0 = D['X'], D['Xt'], D['tr'].y.values, D['te'].y.values, D['it'], D['iv'], D['b0col']
    others = [c for c in D['cols'] if c != b0]
    m0 = fast().fit(X[it], y[it])
    pi = permutation_importance(m0, X[iv], y[iv], scoring='roc_auc', n_repeats=3, random_state=0)
    rank = [c for c in pd.Series(pi.importances_mean, index=D['cols']).sort_values(ascending=False).index if c != b0]
    exp_ = [c for c in EXPERT if c in others]
    for kk in [5, 12, 20]:
        sets = {'ML 선택': [b0] + rank[:kk - 1], '전문가 양식': [b0] + exp_[:kk - 1]}
        for nm, cs in sets.items():
            if len(cs) < kk: continue
            s1 = fast().fit(X[cs], y).predict_proba(Xt[cs])[:, 1]
            s2 = make_pipeline(SimpleImputer(add_indicator=True), StandardScaler(), LogisticRegression(max_iter=2000)).fit(X[cs], y).predict_proba(Xt[cs])[:, 1]
            out['fq'].append(dict(task=k, k=kk, set=nm, auc=roc_auc_score(yt, s1), auc_lr=roc_auc_score(yt, s2), feats=cs))
        rr = np.random.RandomState(kk); aa = []
        for rep in range(3):
            cs = [b0] + list(rr.choice(others, min(kk - 1, len(others)), replace=False))
            aa.append(roc_auc_score(yt, fast().fit(X[cs], y).predict_proba(Xt[cs])[:, 1]))
        out['fq'].append(dict(task=k, k=kk, set='무작위', auc=np.mean(aa), auc_lr=np.nan, feats=None))
    out['fq'].append(dict(task=k, k=len(D['cols']), set='전체', auc=roc_auc_score(yt, fast().fit(X, y).predict_proba(Xt)[:, 1]), auc_lr=np.nan, feats=None))
    out['fq'].append(dict(task=k, k=1, set='지금 소득', auc=roc_auc_score(yt, -D['te'][b0].values), auc_lr=np.nan, feats=None))
print('fq done', flush=True)

# =============== 4. 통합 모델: 학습곡선 · 반복 · 셔플 · 부분의존 · 소득구간 ===============
PK = MAIN + ['KLIPS_r']
ccols = COMMON + ['log_dratio', 'd_log_dratio_2y']
ptr = pd.concat([DATA[k]['tr'].assign(task=k) for k in PK]); pte = pd.concat([DATA[k]['te'].assign(task=k) for k in PK])
for D_ in (ptr, pte):
    for k in PK: D_['pn_' + k] = (D_.task == k).astype(int)
pc = ccols + ['pn_' + k for k in PK]
mkp = lambda n=600: lgb.LGBMClassifier(n_estimators=n, learning_rate=0.03, num_leaves=31, min_child_samples=80, subsample=0.8,
                                       subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=2, random_state=RS)
LC = []; r_ = np.random.RandomState(0)
for frac in [0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 1.0]:
    for rep in range(2 if frac < 1 else 1):
        ii = r_.choice(len(ptr), int(len(ptr) * frac), replace=False)
        m = mkp().fit(ptr[pc].iloc[ii], ptr.y.iloc[ii])
        LC.append(dict(frac=frac, n=len(ii), train_auc=roc_auc_score(ptr.y.iloc[ii], m.predict_proba(ptr[pc].iloc[ii])[:, 1]),
                       test_auc=roc_auc_score(pte.y, m.predict_proba(pte[pc])[:, 1])))
out['lc'] = pd.DataFrame(LC)
mp = mkp(800); ev = {}
mp.fit(ptr[pc], ptr.y, eval_set=[(ptr[pc], ptr.y), (pte[pc], pte.y)], eval_metric='auc', callbacks=[lgb.record_evaluation(ev)])
_ek = list(ev.keys())
out['staged'] = pd.DataFrame(dict(iter=np.arange(1, 801), train_auc=ev[_ek[0]]['auc'], test_auc=ev[_ek[1]]['auc']))
pte['s_pool'] = mp.predict_proba(pte[pc])[:, 1]
out['pool_auc'] = {k: roc_auc_score(g.y, g.s_pool) for k, g in pte.groupby('task')}
out['pool_all'] = roc_auc_score(pte.y, pte.s_pool); out['pool_b0'] = roc_auc_score(pte.y, -pte.log_dratio)
perm = []
for r in range(5):
    m = mkp(300).fit(ptr[pc], ptr.y.sample(frac=1, random_state=r).values); perm.append(roc_auc_score(pte.y, m.predict_proba(pte[pc])[:, 1]))
out['perm'] = perm
bands = []
for lo, hi in [(1.0, 1.25), (1.25, 1.5), (1.5, 2.0), (2.0, 99)]:
    d = pte[(np.exp(pte.log_dratio) >= lo) & (np.exp(pte.log_dratio) < hi)]
    bands.append(dict(lo=lo, hi=hi, n=len(d), pos=d.y.mean(), auc_ml=roc_auc_score(d.y, d.s_pool), auc_b0=roc_auc_score(d.y, -d.log_dratio)))
out['bands'] = pd.DataFrame(bands)
smp = ptr[pc].dropna(subset=['employed', 'd_log_ratio_2y']).sample(6000, random_state=1)
out['pdp_nps'] = partial_dependence(mp, smp, features=('age_to_nps', 'employed'), response_method='predict_proba', method='brute', grid_resolution=20)
out['pdp_d2'] = partial_dependence(mp, smp, features=('log_dratio', 'd_log_ratio_2y'), response_method='predict_proba', method='brute',
                                   grid_resolution=15, percentiles=(0.05, 0.95))
out['pdp_min'] = partial_dependence(mp, smp, features=('log_dratio', 'min_ratio_hist'), response_method='predict_proba', method='brute',
                                    grid_resolution=15, percentiles=(0.05, 0.95))
print('pooled', out['pool_all'], out['pool_b0'], np.round(perm, 3), flush=True)

# =============== 5. 중요도 · 집단별 · 처음 보는 사람 · 보정 ===============
lg_ = lambda q: np.log(np.clip(q, 1e-4, 1 - 1e-4) / (1 - np.clip(q, 1e-4, 1 - 1e-4)))
for k in MAIN + ['KReIS_rn', 'KLIPS_r']:
    D = DATA[k]; m = MODELS[(k, 'LightGBM')]; yt = D['te'].y.values; d = PRED[k]; te = D['te']; tr = D['tr']
    pi = permutation_importance(m, D['Xt'], yt, scoring='roc_auc', n_repeats=5, random_state=0)
    for c, v, s in zip(D['cols'], pi.importances_mean, pi.importances_std): out['imp'].append(dict(task=k, feature=c, imp=v, sd=s))
    G = {'남성': te.female == 0, '여성': te.female == 1, '고졸 미만': te.edu3 == 0, '고졸': te.edu3 == 1, '대졸 이상': te.edu3 == 2,
         '50~59세': te.age < 60, '60~69세': te.age >= 60, '취업': te.employed == 1, '미취업': te.employed == 0,
         '1인 가구': te.hhsize == 1, '2인 이상 가구': te.hhsize >= 2}
    for g, msk in G.items():
        dd = d[msk.values]
        if dd.y.sum() >= 15 and (1 - dd.y).sum() >= 15:
            A_, B_, dl, se, _, _ = delong_diff(dd.y.values, dd['최종: LightGBM+로지스틱'].values, dd['B0 지금 소득'].values)
            out['sub'].append(dict(task=k, group=g, n=len(dd), pos=dd.y.mean(), auc_ml=A_, auc_b0=B_, delta=dl, se=se))
    new = (~te.pid.isin(set(tr.pid)) & ~te.hid.isin(set(tr.hid))).values
    dd = d[new]
    if dd.y.sum() >= 15:
        A_, B_, dl, se, pv_, _ = delong_diff(dd.y.values, dd['최종: LightGBM+로지스틱'].values, dd['B0 지금 소득'].values)
        out['new'].append(dict(task=k, n=len(dd), share=new.mean(), pos=dd.y.mean(), auc_ml=A_, auc_b0=B_, delta=dl, se=se, p=pv_))
    else:
        out['new'].append(dict(task=k, n=int(new.sum()), share=new.mean(), pos=np.nan, auc_ml=np.nan, auc_b0=np.nan, delta=np.nan, se=np.nan, p=np.nan))
    q = m.predict_proba(D['Xt'])[:, 1]
    # Platt 재보정: 학습구간 앞부분으로 학습한 모델의 내부검증 예측으로 보정식 추정 → 시험셋 적용
    m_in = lgb.LGBMClassifier(**m.get_params()).fit(D['X'][D['it']], tr.y.values[D['it']])
    qi = m_in.predict_proba(D['X'][D['iv']])[:, 1]
    pl = LogisticRegression().fit(lg_(qi).reshape(-1, 1), tr.y.values[D['iv']]); q2 = pl.predict_proba(lg_(q).reshape(-1, 1))[:, 1]
    for nm, qq in [('원 확률', q), ('재보정', q2)]:
        b = pd.qcut(qq, 10, labels=False, duplicates='drop')
        for i in np.unique(b): out['cal'].append(dict(task=k, kind=nm, bin=i, pred=qq[b == i].mean(), obs=yt[b == i].mean()))
        ece = sum(abs(qq[b == i].mean() - yt[b == i].mean()) * (b == i).mean() for i in np.unique(b))
        out['calsum'].append(dict(task=k, kind=nm, mean_pred=qq.mean(), obs=yt.mean(), brier=brier_score_loss(yt, qq), ece=ece,
                                  brier_base=brier_score_loss(yt, np.full(len(yt), yt.mean()))))
print('imp/sub/cal done', flush=True)

# =============== 6. 이식: 공통 입력 모델을 다른 패널로 ===============
src = MAIN + ['KLIPS_r', 'KHP_r', 'KLoSA_r']
cc = COMMON + ['log_dratio']
TM, TC = pd.DataFrame(index=src, columns=src, dtype=float), []
for a in src:
    A_ = DATA[a]; m = lgb.LGBMClassifier(n_estimators=500, learning_rate=0.03, num_leaves=15, min_child_samples=80, subsample=0.8,
                                         subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=2, random_state=RS).fit(A_['tr'][cc], A_['tr'].y)
    for b in src:
        Bd = DATA[b]; q = m.predict_proba(Bd['te'][cc])[:, 1]; yb = Bd['te'].y.values
        TM.loc[a, b] = roc_auc_score(yb, q)
        if a != b:
            rec = Bd['tr'][Bd['iv']]; qr = m.predict_proba(rec[cc])[:, 1]
            pl = LogisticRegression().fit(lg_(qr).reshape(-1, 1), rec.y); q2 = pl.predict_proba(lg_(q).reshape(-1, 1))[:, 1]
            TC.append(dict(src=a, tgt=b, auc=TM.loc[a, b], own=np.nan, pred_raw=q.mean(), pred_cal=q2.mean(), obs=yb.mean()))
out['transfer'] = TM; out['transfer_cal'] = pd.DataFrame(TC)
for k in out:
    if isinstance(out[k], list) and out[k] and isinstance(out[k][0], dict): out[k] = pd.DataFrame(out[k])
out['tasks'] = TASKS
out['data_info'] = {k: dict(n_tr=len(D['tr']), n_te=len(D['te']), persons_te=D['te'].pid.nunique(), persons_tr=D['tr'].pid.nunique(),
                            pos_tr=D['tr'].y.mean(), pos_te=D['te'].y.mean(), tr_years=f"{D['tr'].svy_year.min()}–{D['tr'].svy_year.max()}",
                            te_years='·'.join(map(str, sorted(D['te'].svy_year.unique()))), n_feat=len(D['cols']), cols=D['cols'], role=D['role'])
                    for k, D in DATA.items()}
pickle.dump(out, open(W + 'v3_out.pkl', 'wb')); pickle.dump(PRED, open(W + 'v3_pred.pkl', 'wb'))
print('ALL DONE')
