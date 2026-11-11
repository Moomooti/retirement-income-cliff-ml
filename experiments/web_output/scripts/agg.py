import numpy as np, pandas as pd, pickle, json, sys
sys.path.insert(0,'/home/claude/work')
W='/home/claude/work/'
O=pickle.load(open(W+'s_out.pkl','rb')); SFp=pickle.load(open(W+'s_features.pkl','rb'))
o=O[('KOWEPS','S20')]; M,ref=o['M'],o['ref']; G=np.linspace(0,1,1001)
tr,te,_=pickle.load(open(W+'v3_data_KOWEPS_r.pkl','rb')); te=te.reset_index(drop=True).merge(SFp['SF'],on=['panel','pid','svy_year'],how='left')
X=te[M['cols']].astype(float)
for c,(lo,hi) in M['clip'].items(): X[c]=X[c].clip(lo,hi)
sg,sl=M['gbm'].predict_proba(X)[:,1],M['lr'].predict_proba(X)[:,1]
fin=(np.interp(sg,ref['g'],G)+np.interp(sl,ref['l'],G))/2; qf=np.quantile(fin,G)
top=(1-np.interp(fin,qf,G))*100
y=te.y.values; n=len(y)
print('n',n,'rate',y.mean(), 's_log_r sample', te.s_log_r.describe())
bins=[0,10,20,30,40,60,80,100.01]
rows=[]
for a,b in zip(bins[:-1],bins[1:]):
    m=(top>=a)&(top<b); rows.append(dict(lo=a,hi=min(b,100),n=int(m.sum()),rate=float(y[m].mean())))
print(pd.DataFrame(rows))
# income-only rank: low r = high risk
r=np.exp(te.s_log_r.values)
itop=pd.Series(r).rank(pct=True).values*100  # low r -> small pct = top risk
from sklearn.metrics import roc_auc_score
print('auc r only',roc_auc_score(y,-r),'auc model',roc_auc_score(y,fin))
rows2=[]
for a,b in zip(bins[:-1],bins[1:]):
    m=(itop>=a)&(itop<b); rows2.append(dict(lo=a,hi=min(b,100),n=int(m.sum()),rate=float(y[m].mean())))
print(pd.DataFrame(rows2))
rq=np.quantile(r,np.linspace(0,1,101))
print('r quantiles', rq[[0,10,20,50,80,100]])
# minimum cell size check
print('min n', min(x['n'] for x in rows), min(x['n'] for x in rows2))
json.dump(dict(n=n,base=float(y.mean()),model=rows,income=rows2,r_q=[round(float(v),4) for v in rq]),open('/tmp/claude-0/-home-claude/e5872982-71a4-5f1c-953f-30befae32eac/scratchpad/agg.json','w'))
