import numpy as np, pandas as pd, pickle, json, sys
from common_ml import W
OUT = W + 'spkg/mirisaju_model/'; sys.path.insert(0, OUT); from predict import Model
O = pickle.load(open(W + 's_out.pkl', 'rb')); BO = pickle.load(open(W + 'b_out.pkl', 'rb')); m = Model(OUT + 'model'); G = np.linspace(0, 1, 1001)
rng = np.random.RandomState(7); rows = []
for i in range(300):
    hh = int(rng.choice([1, 2, 2, 3, 4])); inc = float(rng.choice(np.arange(60, 900, 10)))
    a = dict(birth_year=int(rng.randint(1956, 1976)), female=int(rng.rand() < .5), married=int(rng.rand() < .7), edu3=int(rng.choice([0, 1, 2])),
             hh_size=hh, hh_size_2y=int(max(1, hh + rng.choice([-1, 0, 0, 0, 1]))), pension_recv=int(rng.rand() < .3), retire_pension=int(rng.rand() < .3),
             private_pension=int(rng.rand() < .4), income_now=inc, income_1y=float(round(inc * rng.uniform(.7, 1.3))), income_2y=float(round(inc * rng.uniform(.6, 1.4))),
             employed=int(rng.rand() < .7), employed_1y=int(rng.rand() < .75), employed_2y=int(rng.rand() < .8),
             job_type=str(rng.choice(['regular', 'temp', 'self', 'other', 'none'])), owner=int(rng.rand() < .7),
             fin_asset=float(rng.choice([0, 500, 2000, 8000, 20000])), real_asset=float(rng.choice([0, 15000, 30000, 60000])), debt=float(rng.choice([0, 1000, 5000, 15000])))
    if rng.rand() < .5: a['health'] = int(rng.randint(1, 6))
    F, r0 = m.features(a)
    exp = dict(eligible=False, top_pct=np.nan, abstain=None)
    if 50 <= F['age'] <= 69 and r0 > 0:
        if r0 >= 1: tag = 'S21' if 'health' in a else 'S20'; o = O[('KOWEPS', tag)]; M, ref = o['M'], o['ref']
        else: tag = 'B20'; M, ref = BO['M'], BO['ref']
        X = pd.DataFrame([F]).reindex(columns=M['cols']).astype(float)
        for c, (lo, hi) in M['clip'].items(): X[c] = X[c].clip(lo, hi)
        sg, sl = M['gbm'].predict_proba(X)[0, 1], M['lr'].predict_proba(X)[0, 1]
        fin = (np.interp(sg, ref['g'], G) + np.interp(sl, ref['l'], G)) / 2
        qf = np.asarray(json.load(open(OUT + f'model/{tag}_meta.json'))['ref_quantiles']['final'])
        exp = dict(eligible=True, top_pct=float((1 - np.interp(fin, qf, G)) * 100), lgb=float(sg), lr=float(sl))
    rows.append(dict(input=json.dumps(a, ensure_ascii=False), **{f'expected_{k}': v for k, v in exp.items()}))
pd.DataFrame(rows).to_csv(OUT + 'parity_cases.csv', index=False)
d = pd.DataFrame(rows); print('합성 300건, 대상(eligible)', int(d.expected_eligible.sum()), '| 그중 기준선 아래', int(sum(1 for x in rows if x['expected_eligible'] and m.features(json.loads(x['input']))[1] < 1)))
