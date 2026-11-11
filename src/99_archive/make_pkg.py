"""백엔드 전달용 모델 패키지 생성 (복지패널 v3 기준 모델)"""
import numpy as np, pandas as pd, pickle, json, ast, os, shutil, joblib, sklearn
import lightgbm as lgb
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from common_ml import W, CATEG

K = 'KOWEPS_r'; OUT = W + 'pkg/mirinohu_model/'
shutil.rmtree(W + 'pkg', ignore_errors=True); os.makedirs(OUT + 'model')
tr, te, cols = pickle.load(open(W + 'v3_data_KOWEPS_r.pkl', 'rb')); tr, te = tr.reset_index(drop=True), te.reset_index(drop=True)
X, Xt = tr[cols].astype(float), te[cols].astype(float); y, yt = tr.y.values, te.y.values
clip = {}
for c in cols:
    if c in CATEG or X[c].nunique() <= 3: continue
    lo, hi = X[c].quantile([0.005, 0.995]); clip[c] = [float(lo), float(hi)]; X[c] = X[c].clip(lo, hi); Xt[c] = Xt[c].clip(lo, hi)
cat = [c for c in cols if c in CATEG]; num = [c for c in cols if c not in CATEG]
prep = ColumnTransformer([('n', make_pipeline(SimpleImputer(strategy='median', add_indicator=True), StandardScaler()), num),
                          ('c', make_pipeline(SimpleImputer(strategy='constant', fill_value=-1),
                                              OneHotEncoder(handle_unknown='infrequent_if_exist', min_frequency=50, sparse_output=False)), cat)])
lr = make_pipeline(prep, LogisticRegression(C=1.0, max_iter=3000)).fit(X, y)
TU = pd.DataFrame(pickle.load(open(W + 'v3_out.pkl', 'rb'))['tune']); t = TU[(TU.task == K) & (TU.model == 'LightGBM')].iloc[0]
prm = t.params if isinstance(t.params, dict) else ast.literal_eval(t.params)
gbm = lgb.LGBMClassifier(n_estimators=int(t.iters), learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                         verbose=-1, n_jobs=2, random_state=42, **prm).fit(X, y)
s_g, s_l = gbm.predict_proba(Xt)[:, 1], lr.predict_proba(Xt)[:, 1]
PRED = pickle.load(open(W + 'v3_pred.pkl', 'rb'))[K]
print('재현 확인: LGBM 최대차', np.abs(s_g - PRED['LightGBM'].values).max(), ' LR 최대차', np.abs(s_l - PRED['LR_L2'].values).max())
fin_rank = rankdata(s_g) + rankdata(s_l)
# 1명 채점용 기준 분포(시험 기간 점수의 분위수, 집계값)
Q = np.linspace(0, 1, 1001)
qg, ql = np.quantile(s_g, Q), np.quantile(s_l, Q)
pct = lambda s, q: np.interp(s, q, Q)
fin = (pct(s_g, qg) + pct(s_l, ql)) / 2
qf = np.quantile(fin, Q)
print('AUC  LGBM', roc_auc_score(yt, s_g), ' LR', roc_auc_score(yt, s_l), ' 순위평균(v3)', roc_auc_score(yt, fin_rank), ' 분위수평균(서비스식)', roc_auc_score(yt, fin))
gbm.booster_.save_model(OUT + 'model/lgb_model.txt')
joblib.dump(lr, OUT + 'model/lr_pipeline.joblib')
top = 1 - pct(fin, qf); hi = top <= 0.2
meta = dict(model='mirinohu-koweps-v3', task='지금 빈곤선 위인 50~69세가 1~4년 뒤 3번 중 2번 이상 가처분 빈곤선 아래(복지패널)',
            features=cols, categorical=cat, clip=clip, quantile_grid_n=1001,
            ref_quantiles=dict(lgb=qg.tolist(), lr=ql.tolist(), final=qf.tolist()),
            bands=dict(high='상위 20% 이내', mid='상위 20~40%', low='그 밖'),
            test=dict(years=sorted(te.svy_year.unique().tolist()), n=int(len(yt)), base_rate=float(yt.mean()), auc_lgb=float(roc_auc_score(yt, s_g)),
                      auc_lr=float(roc_auc_score(yt, s_l)), auc_final=float(roc_auc_score(yt, fin)), rate_in_high=float(yt[hi].mean())),
            train=dict(years=[int(tr.svy_year.min()), int(tr.svy_year.max())], n=int(len(y))),
            versions=dict(lightgbm=lgb.__version__, sklearn=sklearn.__version__, numpy=np.__version__, pandas=pd.__version__))
json.dump(meta, open(OUT + 'model/meta.json', 'w'), ensure_ascii=False)
# ---- 합성 일치 테스트 입력 (실제 사람 아님: 열마다 독립적으로 분포에서 뽑음) ----
rng = np.random.RandomState(2026); n = 300; S = {}
for c in cols:
    v = te[c].astype(float); miss = v.isna().mean(); vv = v.dropna()
    if vv.nunique() <= 12: col = rng.choice(vv.value_counts(normalize=True).index.values, n, p=vv.value_counts(normalize=True).values)
    else: col = np.interp(rng.uniform(0.02, 0.98, n), np.linspace(0, 1, 101), np.quantile(vv, np.linspace(0, 1, 101)))
    col = col.astype(float); col[rng.rand(n) < miss] = np.nan; S[c] = col
S = pd.DataFrame(S)[cols]; Sc = S.copy()
for c, (lo, hi_) in clip.items(): Sc[c] = Sc[c].clip(lo, hi_)
eg, el = gbm.predict_proba(Sc)[:, 1], lr.predict_proba(Sc)[:, 1]; ef = (pct(eg, qg) + pct(el, ql)) / 2; et = 1 - pct(ef, qf)
P = S.copy(); P['expected_lgb'] = eg; P['expected_lr'] = el; P['expected_final'] = ef; P['expected_top_pct'] = et * 100
P.to_csv(OUT + 'parity_cases.csv', index=False, float_format='%.10g')
print('합성 300줄 저장, 상위20% 비율', (et <= 0.2).mean())
