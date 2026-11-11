import numpy as np, pandas as pd, pickle, warnings
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score
from common_ml import *
warnings.filterwarnings('ignore')
pr = pickle.load(open(W + 'label_v3_preds.pkl', 'rb'))
for k, d in pr.items():
    ens = rankdata(d.ml) + rankdata(d.lr)
    print(k, 'ML', round(roc_auc_score(d.y, d.ml), 3), 'LR', round(roc_auc_score(d.y, d.lr), 3), 'ENS', round(roc_auc_score(d.y, ens), 3))
