"""검증 보강: (a) 사람 단위 클러스터 부트스트랩 (b) 처음 보는 사람 (c) 집단별 (d) 질문 수 고정 비교
(e) 국민노후패널 현장 기준선(충족률·걱정) (f) 패널 간 이식 시 확률 재보정."""
import numpy as np, pandas as pd, pickle, warnings
from common_ml import *
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
warnings.filterwarnings('ignore')
S = pd.read_pickle(W + 'analytic.pkl')
out = {}
TR, TE, PR, MT = {}, {}, {}, {}
for p in PANELS:
    tr, te = split(S, p); EX = extra_features(tr); te = add_logs(te, EX)
    TR[p], TE[p] = tr, te
    d = pd.read_pickle(W + f'preds_{p}.pkl'); g3 = pd.read_pickle(W + f'preds_gbm3_{p}.pkl')
    for c in g3: d[c] = g3[c].values
    assert (d.pid.values == te.pid.values).all()
    PR[p] = d; MT[p] = pickle.load(open(W + f'meta_{p}.pkl', 'rb'))
ML = 'full|HGB_tuned'

# (a) 사람 단위 클러스터 부트스트랩
rng = np.random.RandomState(7); boot = []
for p in PANELS:
    d = PR[p]; pids = d.pid.unique(); idx = d.groupby('pid').indices
    for comp, a, b in [('ML−소득', ML, 'B0_income_only'), ('ML−계산기', ML, 'B1_calculator'), ('ML−로지스틱', ML, 'full|LR_L2'),
                       ('로지스틱−소득', 'full|LR_L2', 'B0_income_only')]:
        ds = []
        for r in range(400):
            ii = np.concatenate([idx[k] for k in rng.choice(pids, len(pids))])
            yy = d.y.values[ii]
            ds.append(roc_auc_score(yy, d[a].values[ii]) - roc_auc_score(yy, d[b].values[ii]))
        est = roc_auc_score(d.y, d[a]) - roc_auc_score(d.y, d[b])
        boot.append(dict(panel=p, comp=comp, delta=est, se=np.std(ds), lo=np.percentile(ds, 2.5), hi=np.percentile(ds, 97.5)))
B = pd.DataFrame(boot); out['boot'] = B
out['boot_meta'] = {c: meta_dl(g.delta, g.se) for c, g in B.groupby('comp')}
print(B.round(4).to_string()); print({k: round(v['est'], 4) for k, v in out['boot_meta'].items()})

# (b) 처음 보는 사람 · 처음 보는 가구
nw = []
for p in PANELS:
    d, tr, te = PR[p], TR[p], TE[p]
    new = (~te.pid.isin(set(tr.pid)) & ~te.hid.isin(set(tr.hid))).values
    dd = d[new]
    if dd.y.sum() >= 20:
        A_, B_, dl, se, pv_, _ = delong_diff(dd.y.values, dd[ML].values, dd['B0_income_only'].values)
        nw.append(dict(panel=p, n=len(dd), share=new.mean(), pos=dd.y.mean(), auc_ml=A_, auc_b0=B_, delta=dl, se=se, p=pv_))
out['new_people'] = pd.DataFrame(nw)
out['new_meta'] = meta_dl(out['new_people'].delta, out['new_people'].se) if len(nw) >= 2 else None
print('new people panels', len(nw))
print(out['new_people'].round(3).to_string() if len(nw) else 'none')

# (c) 집단별
sg = []
for p in PANELS:
    d, te = PR[p], TE[p]
    groups = {'남성': te.female.values == 0, '여성': te.female.values == 1, '고졸 미만': te.edu3.values == 0,
              '고졸': te.edu3.values == 1, '대졸 이상': te.edu3.values == 2, '50~59세': te.age.values < 60,
              '60~69세': te.age.values >= 60, '취업': te.employed.values == 1, '미취업': te.employed.values == 0}
    for g, m in groups.items():
        dd = d[m]
        if dd.y.sum() >= 15 and (1 - dd.y).sum() >= 15:
            A_, B_, dl, se, pv_, _ = delong_diff(dd.y.values, dd[ML].values, dd['B0_income_only'].values)
            sg.append(dict(panel=p, group=g, n=len(dd), auc_ml=A_, auc_b0=B_, delta=dl, se=se))
SG = pd.DataFrame(sg); out['subgroup'] = SG
out['subgroup_meta'] = pd.DataFrame([dict(group=g, k=len(x), **meta_dl(x.delta, x.se),
                                          auc_ml=x.auc_ml.mean(), auc_b0=x.auc_b0.mean()) for g, x in SG.groupby('group', sort=False)])
print(out['subgroup_meta'][['group', 'k', 'auc_b0', 'auc_ml', 'est', 'lo', 'hi']].round(3).to_string())

# (d) 질문 수 고정: ML이 고른 k개 vs 전문가 양식 k개 vs 무작위 k개 (모두 '지금 소득' 포함)
EXPERT = ['log_ratio', 'age', 'employed', 'married', 'hhsize', 'x_pension_recv', 'x_pension_enrolled', 'x_owner',
          'lg_x_fin_assets', 'lg_x_debt', 'lg_x_net_assets', 'x_health_bad', 'x_chronic', 'edu3', 'female',
          'x_regular', 'x_selfemp', 'x_private_pension', 'x_retire_pension', 'x_occ', 'x_region', 'x_need_min',
          'lg_x_realestate', 'lg_x_house_value', 'x_temp_daily', 'employed_l2', 'd_log_ratio_2y']
fq = []
for p in PANELS:
    tr, te = TR[p], TE[p]; mm = MT[p]['meta']['full']; cols = mm['cols']; prm = mm['best'][1]; nit = int(mm['best'][2] * 1.1)
    Xtr, Xte = mm['Xtr'], mm['Xte']; y = tr.y.values; yt = te.y.values
    vy = sorted(tr.svy_year.unique())[-2:]; iv = tr.svy_year.isin(vy).values; it = (tr.svy_year <= min(vy) - 2).values
    cat = lambda cs: [c in CATEG for c in cs]
    # 질문 수 비교는 모든 묶음에 같은 고정 설정(빠른 HGB)을 써서 공정하게 비교
    mk = lambda cs: HistGradientBoostingClassifier(learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=100,
                                                   l2_regularization=1.0, max_iter=300, random_state=42, categorical_features=cat(cs))
    m0 = mk(cols).fit(Xtr[it], y[it])     # 순위는 학습구간 안의 내부 검증으로만 정한다
    pi = permutation_importance(m0, Xtr[iv], y[iv], scoring='roc_auc', n_repeats=3, random_state=0)
    rank = [c for c in pd.Series(pi.importances_mean, index=cols).sort_values(ascending=False).index if c != 'log_ratio']
    exp_ = [c for c in EXPERT if c in cols and c != 'log_ratio']
    others = [c for c in cols if c != 'log_ratio']
    for k in [5, 12, 20]:
        if k - 1 > len(others): continue
        sets = {'ML 선택': ['log_ratio'] + rank[:k - 1], '전문가 양식': ['log_ratio'] + exp_[:k - 1]}
        for nm, cs in sets.items():
            if len(cs) < k: continue
            s_ = mk(cs).fit(Xtr[cs], y).predict_proba(Xte[cs])[:, 1]
            lr = make_pipeline(SimpleImputer(add_indicator=True), StandardScaler(), LogisticRegression(max_iter=2000))
            s2 = lr.fit(Xtr[cs].astype(float), y).predict_proba(Xte[cs].astype(float))[:, 1]
            fq.append(dict(panel=p, k=k, set=nm, auc=roc_auc_score(yt, s_), auc_lr=roc_auc_score(yt, s2), feats=cs))
        r_ = np.random.RandomState(k)
        aa = []
        for rep in range(3):
            cs = ['log_ratio'] + list(r_.choice(others, k - 1, replace=False))
            aa.append(roc_auc_score(yt, mk(cs).fit(Xtr[cs], y).predict_proba(Xte[cs])[:, 1]))
        fq.append(dict(panel=p, k=k, set='무작위', auc=np.mean(aa), auc_lr=np.nan, feats=None))
    fq.append(dict(panel=p, k=len(cols), set='전체', auc=roc_auc_score(yt, mk(cols).fit(Xtr, y).predict_proba(Xte)[:, 1]), auc_lr=roc_auc_score(yt, PR[p]['full|LR_L2']), feats=None))
    fq.append(dict(panel=p, k=1, set='지금 소득', auc=roc_auc_score(yt, PR[p]['B0_income_only']), auc_lr=np.nan, feats=None))
FQ = pd.DataFrame(fq); out['fixedq'] = FQ
print(FQ.pivot_table(index=['k', 'set'], values=['auc', 'auc_lr'], aggfunc='mean').round(3))
out['top_ml_feats'] = {p: FQ[(FQ.panel == p) & (FQ.k == 12) & (FQ.set == 'ML 선택')].feats.iloc[0] for p in PANELS
                       if len(FQ[(FQ.panel == p) & (FQ.k == 12) & (FQ.set == 'ML 선택')])}

# (e) 국민노후패널: 현장 판단 기준선
d, te = PR['KReIS'].copy(), TE['KReIS']
d['cover'] = te.x_cover_ratio.values; d['worry'] = te.x_worry.values
fb = []
for nm, col, sub in [('지금 소득', 'B0_income_only', d.cover.notna()), ('계산(충족률)', 'cover', d.cover.notna()),
                     ('본인 걱정', 'worry', d.worry.notna())]:
    dd = d[sub & d[col if col != 'cover' else 'cover'].notna()]
    sc = -dd.cover if col == 'cover' else dd[col]
    A_, B_, dl, se, pv_, _ = delong_diff(dd.y.values, dd[ML].values, sc.values)
    k20 = int(len(dd) * 0.2)
    found = lambda s: dd.y.values[np.argsort(-np.asarray(s))[:k20]].sum()
    fb.append(dict(base=nm, n=len(dd), pos=int(dd.y.sum()), auc_base=B_, auc_ml=A_, delta=dl, se=se, p=pv_, k20=k20,
                   found_base=found(sc.values), found_ml=found(dd[ML].values)))
out['field'] = pd.DataFrame(fb); print(out['field'].round(3).to_string())

# (f) 이식: 그대로 vs 확률만 재보정(Platt, 대상 패널의 학습구간 마지막 2개 연도) vs 대상 패널에서 재학습
HP = dict(learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=100, l2_regularization=1.0, max_iter=400)
lg = lambda q: np.log(np.clip(q, 1e-4, 1 - 1e-4) / (1 - np.clip(q, 1e-4, 1 - 1e-4)))
tf = []
for a in PANELS:
    m = HistGradientBoostingClassifier(random_state=42, **HP).fit(TR[a][COMMON], TR[a].y)
    for b in PANELS:
        if a == b: continue
        tb = TR[b]; rec = tb[tb.svy_year.isin(sorted(tb.svy_year.unique())[-2:])]
        q_rec = m.predict_proba(rec[COMMON])[:, 1]; q = m.predict_proba(TE[b][COMMON])[:, 1]
        pl = LogisticRegression().fit(lg(q_rec).reshape(-1, 1), rec.y); q2 = pl.predict_proba(lg(q).reshape(-1, 1))[:, 1]
        yb = TE[b].y.values
        tf.append(dict(src=a, tgt=b, auc=roc_auc_score(yb, q), pred_raw=q.mean(), pred_cal=q2.mean(), obs=yb.mean()))
TF = pd.DataFrame(tf); out['transfer_cal'] = TF
print(TF.assign(err_raw=(TF.pred_raw - TF.obs).abs(), err_cal=(TF.pred_cal - TF.obs).abs())[['err_raw', 'err_cal']].describe().round(3))
pickle.dump(out, open(W + 'extra_out.pkl', 'wb'))
print('DONE extra')
