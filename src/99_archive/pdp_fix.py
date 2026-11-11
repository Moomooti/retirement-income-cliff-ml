import numpy as np, pandas as pd, pickle, warnings
from common_ml import *
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import partial_dependence
warnings.filterwarnings('ignore')
S = pd.read_pickle(W + 'analytic.pkl')
TR = [split(S, p)[0] for p in PANELS]; ptr = pd.concat(TR)
for c in PANELS: ptr['pn_' + c] = (ptr.panel == c).astype(int)
pc = COMMON + ['pn_' + c for c in PANELS]
m = HistGradientBoostingClassifier(learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=100, l2_regularization=1.0,
                                   max_iter=600, random_state=42).fit(ptr[pc], ptr.y)
smp = ptr[pc].dropna(subset=['employed', 'vol_hist', 'd_log_ratio_2y']).sample(8000, random_state=1)
o = {}
o['age_emp'] = partial_dependence(m, smp, features=('age', 'employed'), response_method='predict_proba', method='brute', grid_resolution=20)
o['ratio_vol'] = partial_dependence(m, smp, features=('log_ratio', 'vol_hist'), response_method='predict_proba', method='brute',
                                    grid_resolution=15, percentiles=(0.02, 0.95))
o['ratio_d2'] = partial_dependence(m, smp, features=('log_ratio', 'd_log_ratio_2y'), response_method='predict_proba', method='brute',
                                   grid_resolution=15, percentiles=(0.05, 0.95))
o['agenps_emp'] = partial_dependence(m, smp, features=('age_to_nps', 'employed'), response_method='predict_proba', method='brute', grid_resolution=20)
pickle.dump(o, open(W + 'pdp.pkl', 'wb'))
for k, v in o.items():
    print(k, [np.round(g, 2) for g in v['grid_values']]); print(np.round(v['average'][0], 3))
