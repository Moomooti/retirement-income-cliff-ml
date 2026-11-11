"""패널별 모델 비교 (신경망 제외). 사용: python run_models.py PANEL"""
import sys, time, warnings, pickle
import numpy as np, pandas as pd
from common_ml import *
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder, SplineTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression, RidgeClassifier, SGDClassifier
from sklearn.svm import LinearSVC, SVC
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (RandomForestClassifier, ExtraTreesClassifier, BaggingClassifier, AdaBoostClassifier,
                              GradientBoostingClassifier, HistGradientBoostingClassifier, VotingClassifier,
                              StackingClassifier)
from sklearn.kernel_approximation import Nystroem
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF, ConstantKernel
warnings.filterwarnings('ignore')
RS = 42
P = sys.argv[1]
S = pd.read_pickle(W + 'analytic.pkl')
tr, te = split(S, P)
EX = extra_features(tr); te = add_logs(te, EX)
FS = {'common': COMMON, 'full': COMMON + EX}


def winsor(tr, te, cols):
    for c in cols:
        if c in CATEG or tr[c].nunique() <= 3: continue
        lo, hi = tr[c].quantile([0.005, 0.995])
        tr[c] = tr[c].clip(lo, hi); te[c] = te[c].clip(lo, hi)


def prep(cols, spline=False):
    num = [c for c in cols if c not in CATEG]; cat = [c for c in cols if c in CATEG]
    nump = [SimpleImputer(strategy='median', add_indicator=True), StandardScaler()]
    if spline:
        nump = [SimpleImputer(strategy='median', add_indicator=True), StandardScaler(),
                SplineTransformer(n_knots=5, degree=3, extrapolation='linear')]
    t = [('n', make_pipeline(*nump), num)]
    if cat:
        t.append(('c', make_pipeline(SimpleImputer(strategy='constant', fill_value=-1),
                                     OneHotEncoder(handle_unknown='infrequent_if_exist', min_frequency=50,
                                                   sparse_output=False)), cat))
    return ColumnTransformer(t)


def score(m, X):
    if hasattr(m, 'predict_proba'):
        try: return m.predict_proba(X)[:, 1]
        except Exception: pass
    return m.decision_function(X)


def tune_hgb(Xtr, ytr, years, cat_mask):
    """사전 등록한 격자. 학습구간 마지막 2개 기준연도를 내부 검증으로 사용(시간 순서 유지)."""
    vy = sorted(years.unique())[-2:]
    iv = years.isin(vy).values; it = years <= min(vy) - 2
    grid = [dict(learning_rate=lr, max_leaf_nodes=ml, min_samples_leaf=msl, l2_regularization=l2)
            for lr in (0.03, 0.06) for ml in (15, 31) for msl in (40, 150) for l2 in (0.0, 1.0)]
    best = None
    for g in grid:
        m = HistGradientBoostingClassifier(max_iter=1500, early_stopping=True, validation_fraction=0.15,
                                           n_iter_no_change=50, random_state=RS, categorical_features=cat_mask, **g)
        m.fit(Xtr[it.values], ytr[it.values])
        a = roc_auc_score(ytr[iv], m.predict_proba(Xtr[iv])[:, 1])
        if best is None or a > best[0]: best = (a, g, m.n_iter_)
    return best


res = []
preds = {'y': te.y.values, 'svy_year': te.svy_year.values, 'pid': te.pid.values, 'age': te.age.values,
         'log_ratio': te.log_ratio.values, 'employed': te.employed.values}
preds['B0_income_only'] = -te.log_ratio.values
calc = make_pipeline(SimpleImputer(), StandardScaler(), LogisticRegression())
calc.fit(tr[['log_ratio', 'age', 'employed']], tr.y)
preds['B1_calculator'] = calc.predict_proba(te[['log_ratio', 'age', 'employed']])[:, 1]
for k in ['B0_income_only', 'B1_calculator']:
    res.append(dict(panel=P, fs='baseline', model=k, auc=roc_auc_score(te.y, preds[k]), sec=0))
print(P, 'train', tr.shape, 'test', te.shape, 'B0', res[0]['auc'], flush=True)
meta = {}
for fs, cols in FS.items():
    Xtr, Xte = tr[cols].copy(), te[cols].copy(); ytr = tr.y.values
    winsor(Xtr, Xte, cols)
    cat_mask = [c in CATEG for c in cols]
    t0 = time.time(); best = tune_hgb(Xtr, pd.Series(ytr, index=Xtr.index), tr.svy_year, cat_mask)
    print(fs, 'HGB tuned', best, round(time.time() - t0), flush=True)
    hgb_best = HistGradientBoostingClassifier(max_iter=max(50, int(best[2] * 1.1)), early_stopping=False,
                                              random_state=RS, categorical_features=cat_mask, **best[1])
    pp = lambda: prep(cols)
    M = {
        'HGB_tuned': hgb_best,
        'LR_L2': make_pipeline(pp(), LogisticRegression(C=1.0, max_iter=3000)),
        'LR_L1': make_pipeline(pp(), LogisticRegression(penalty='l1', C=0.1, solver='liblinear')),
        'LR_ElasticNet': make_pipeline(pp(), LogisticRegression(penalty='elasticnet', l1_ratio=0.5, C=0.5,
                                                                solver='saga', max_iter=3000)),
        'LR_Spline_GAM': make_pipeline(prep(cols, spline=True), LogisticRegression(C=0.3, max_iter=3000)),
        'HGB_default': HistGradientBoostingClassifier(random_state=RS, categorical_features=cat_mask),
        'HGB_additive': HistGradientBoostingClassifier(max_iter=max(50, int(best[2] * 1.1)), random_state=RS,
                                                       interaction_cst='no_interactions', early_stopping=False,
                                                       categorical_features=cat_mask, **best[1]),
        'RandomForest': make_pipeline(pp(), RandomForestClassifier(n_estimators=400, min_samples_leaf=20,
                                                                   max_features='sqrt', n_jobs=2, random_state=RS)),
        'ExtraTrees': make_pipeline(pp(), ExtraTreesClassifier(n_estimators=400, min_samples_leaf=20,
                                                               max_features=0.5, n_jobs=2, random_state=RS)),
    }
    if fs == 'full':
        M.update({
            'RidgeClassifier': make_pipeline(pp(), RidgeClassifier(alpha=10)),
            'SGD_LogLoss': make_pipeline(pp(), SGDClassifier(loss='log_loss', alpha=1e-3, random_state=RS)),
            'LinearSVM': make_pipeline(pp(), LinearSVC(C=0.05, dual=False)),
            'LDA': make_pipeline(pp(), LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')),
            'QDA': make_pipeline(pp(), QuadraticDiscriminantAnalysis(reg_param=0.5)),
            'GaussianNB': make_pipeline(pp(), GaussianNB()),
            'KNN_k101': make_pipeline(pp(), KNeighborsClassifier(n_neighbors=101, weights='distance', n_jobs=2)),
            'DecisionTree': make_pipeline(pp(), DecisionTreeClassifier(max_depth=6, min_samples_leaf=50,
                                                                       random_state=RS)),
            'Bagging_Tree': make_pipeline(pp(), BaggingClassifier(DecisionTreeClassifier(max_depth=8,
                                                                                         min_samples_leaf=20),
                                                                  n_estimators=150, n_jobs=2, random_state=RS)),
            'AdaBoost': make_pipeline(pp(), AdaBoostClassifier(n_estimators=300, learning_rate=0.5,
                                                               random_state=RS)),
            'GradientBoosting': make_pipeline(pp(), GradientBoostingClassifier(n_estimators=300, max_depth=3,
                                                                               learning_rate=0.05, subsample=0.8,
                                                                               random_state=RS)),
            'SVM_RBF_6k': 'svc', 'Nystroem_RBF_LR': make_pipeline(pp(), Nystroem(gamma=0.02, n_components=600,
                                                                                 random_state=RS),
                                                                  LogisticRegression(C=0.5, max_iter=3000)),
            'GaussianProcess_2k': 'gpc',
            'Voting_soft': 'vote', 'Stacking': 'stack',
        })
    for name, m in M.items():
        t0 = time.time()
        try:
            if m == 'svc':
                idx = np.random.RandomState(RS).choice(len(Xtr), min(6000, len(Xtr)), replace=False)
                m = make_pipeline(pp(), SVC(C=1.0, gamma='scale')); m.fit(Xtr.iloc[idx], ytr[idx])
            elif m == 'gpc':
                idx = np.random.RandomState(RS).choice(len(Xtr), min(2000, len(Xtr)), replace=False)
                m = make_pipeline(pp(), GaussianProcessClassifier(1.0 * RBF(5.0), random_state=RS))
                m.fit(Xtr.iloc[idx], ytr[idx])
            elif m == 'vote':
                m = VotingClassifier([('lr', M['LR_Spline_GAM']), ('rf', M['RandomForest']), ('hgb', hgb_best)],
                                     voting='soft'); m.fit(Xtr, ytr)
            elif m == 'stack':
                m = StackingClassifier([('gam', M['LR_Spline_GAM']), ('rf', M['RandomForest']),
                                        ('et', M['ExtraTrees']), ('hgb', hgb_best)],
                                       final_estimator=LogisticRegression(), cv=3, n_jobs=1)
                m.fit(Xtr, ytr)
            else:
                m.fit(Xtr, ytr)
            s = score(m, Xte); a = roc_auc_score(te.y, s)
            preds[f'{fs}|{name}'] = s
            if name == 'HGB_tuned': meta[fs] = dict(model=m, cols=cols, best=best, Xtr=Xtr, Xte=Xte)
        except Exception as e:
            a = np.nan; print('ERR', name, e)
        res.append(dict(panel=P, fs=fs, model=name, auc=a, sec=round(time.time() - t0, 1)))
        print(f'{fs:7s} {name:20s} AUC={a:.4f} ({time.time() - t0:.0f}s)', flush=True)
pd.DataFrame(res).to_csv(W + f'res_{P}.csv', index=False)
pd.DataFrame(preds).to_pickle(W + f'preds_{P}.pkl')
pickle.dump(dict(meta=meta, EX=EX, n_tr=len(tr), n_te=len(te), pos_tr=tr.y.mean(), pos_te=te.y.mean()),
            open(W + f'meta_{P}.pkl', 'wb'))
print('DONE', P)
