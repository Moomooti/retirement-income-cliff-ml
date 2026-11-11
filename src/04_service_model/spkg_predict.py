"""미리사주 서비스 모델 예측 모듈 – 화면 21문항을 그대로 받는다.

사용법
    from predict import Model
    m = Model('model')
    m.predict({...화면 입력...})          # dict 1개 → 결과 dict 1개

입력 (금액: 만원, 소득: 가구 월 실수령 = 세후)
    birth_year, female(0/1), married(0/1), edu3(0 고졸 미만·1 고졸·2 대졸 이상),
    hh_size, hh_size_2y, pension_recv(0/1), retire_pension(0/1), private_pension(0/1),
    income_now, income_1y, income_2y, employed(0/1), employed_1y(0/1), employed_2y(0/1),
    job_type('regular'|'temp'|'self'|'other'|'none'), owner(0/1), fin_asset, real_asset, debt,
    health(1 매우 건강 ~ 5 매우 나쁨, 선택: 없거나 None이면 건강 제외 모델 사용)
출력
    eligible, reason, mode, band(high/mid/low), top_pct, abstain, reasons[{feature,label,effect}], model, ratio_now
    mode = 'above' : 지금 기준선 위 → 2년 뒤 반복해서 기준선 아래로 내려갈 쪽의 순위 (S20/S21)
    mode = 'below' : 지금 기준선 아래 → 2년 뒤에도 기준선 아래에 머물 쪽의 순위 (B20, prereg_B.txt 통과)
    band high = 그 방향(내려감/머묾) 신호가 많은 상위 20%, mid = 20~40%, low = 나머지
"""
import json, os
import numpy as np, pandas as pd, joblib, lightgbm as lgb

LABELS = {
    'age': '나이', 'age_to_60': '60세까지 남은 기간', 'age_to_nps': '국민연금 받기까지 남은 기간', 'female': '성별', 'married': '배우자',
    'edu3': '학력', 'hhsize': '가구원 수', 's_hhchg': '최근 2년 가구원 변화', 'x_pension_recv': '공적연금 수령',
    'x_retire_pension': '퇴직연금', 'x_private_pension': '개인연금', 's_log_r': '지금 소득(빈곤선 대비)', 's_d1': '1년 사이 소득 변화',
    's_d2': '2년 사이 소득 변화', 's_min3': '최근 3년 중 가장 낮았던 소득', 's_vol3': '최근 3년 소득 출렁임', 'employed': '지금 일함',
    's_emp_l1': '1년 전 일함', 's_emp_l2': '2년 전 일함', 's_lost': '최근 2년 내 일을 그만둠', 'x_regular': '상용직', 'x_temp_daily': '임시·일용직',
    'x_selfemp': '자영업', 's_owner': '자가', 's_fin_r': '금융자산(소득 대비)', 's_debt_r': '부채(소득 대비)', 's_real_r': '부동산(소득 대비)',
    's_lg_fin': '금융자산', 's_lg_debt': '부채', 's_lg_real': '부동산', 's_health': '건강',
}
JOB = {'regular': (1, 0, 0), 'temp': (0, 1, 0), 'self': (0, 0, 1), 'other': (0, 0, 0), 'none': (0, 0, 0)}


class _One:
    def __init__(self, d, tag):
        self.meta = json.load(open(os.path.join(d, f'{tag}_meta.json'), encoding='utf-8'))
        self.cols, self.clip = self.meta['features'], self.meta['clip']
        self.gbm = lgb.Booster(model_file=os.path.join(d, f'{tag}_lgb.txt'))
        self.mc = lgb.Booster(model_file=os.path.join(d, f'{tag}_lgb_conformal.txt'))
        self.lr = joblib.load(os.path.join(d, f'{tag}_lr.joblib'))
        q = self.meta['ref_quantiles']; self.G = np.linspace(0, 1, len(q['lgb'])); self.qg, self.ql, self.qf = map(np.asarray, (q['lgb'], q['lr'], q['final']))

    def run(self, F):
        X = pd.DataFrame([F]).reindex(columns=self.cols).astype(float)
        for c, (lo, hi) in self.clip.items(): X[c] = X[c].clip(lo, hi)
        sg = self.gbm.predict(X)[0]; sl = self.lr.predict_proba(X)[0, 1]
        fin = (np.interp(sg, self.qg, self.G) + np.interp(sl, self.ql, self.G)) / 2
        top = 1 - np.interp(fin, self.qf, self.G)
        sc = self.mc.predict(X)[0]; abstain = bool((1 - sc) <= self.meta['conformal']['q1'] and sc <= self.meta['conformal']['q0'])
        con = self.gbm.predict(X, pred_contrib=True)[0, :-1]; idx = np.argsort(-np.abs(con))[:3]
        return dict(lgb=float(sg), lr=float(sl), final=float(fin), top_pct=float(top * 100),
                    band='high' if top <= 0.2 else 'mid' if top <= 0.4 else 'low', abstain=abstain,
                    reasons=[dict(feature=self.cols[j], label=LABELS.get(self.cols[j], self.cols[j]), effect=float(con[j])) for j in idx])


class Model:
    def __init__(self, model_dir):
        self.m20, self.m21 = _One(model_dir, 'S20'), _One(model_dir, 'S21')
        self.b20 = _One(model_dir, 'B20') if os.path.exists(os.path.join(model_dir, 'B20_meta.json')) else None
        c = json.load(open(os.path.join(model_dir, 'constants.json'), encoding='utf-8'))
        self.line = {int(k): v for k, v in c['poverty_line_2023won'].items()}; self.cpi = {int(k): v for k, v in c['cpi'].items()}
        self.ref_year = c['default_income_year']

    def _cpi(self, y): return self.cpi.get(y, self.cpi[max(self.cpi)])          # 자료 없는 해는 최신 CPI로
    def _line(self, y): return self.line.get(y, self.line[max(self.line)])       # 자료 없는 해는 최신 빈곤선(실질 동일 가정)

    def features(self, a, income_year=None):
        Y = income_year or self.ref_year              # '지금' 소득의 소득연도
        hh = float(np.clip(a['hh_size'], 1, 10)); hh2 = float(np.clip(a.get('hh_size_2y', hh), 1, 10))
        def r(m, y, h):                                 # 월 실수령(명목) → 연 → 2023년 가격 → 균등화 → 빈곤선 대비
            if m is None or m <= 0: return np.nan
            return m * 12 * self._cpi(2023) / self._cpi(y) / np.sqrt(h) / self._line(y)
        r0, r1, r2 = r(a['income_now'], Y, hh), r(a.get('income_1y'), Y - 1, hh), r(a.get('income_2y'), Y - 2, hh2)
        L = np.log([v if v == v and v > 0 else np.nan for v in (r0, r1, r2)])
        ok = L[~np.isnan(L)]
        age = Y - a['birth_year']; b = a['birth_year'] + 1      # 학습 데이터의 출생연도 근사(소득연도+1−나이)와 맞춤
        nps = 60 if b <= 1952 else 61 if b <= 1956 else 62 if b <= 1960 else 63 if b <= 1964 else 64 if b <= 1968 else 65
        reg, tmp, slf = JOB.get(a.get('job_type', 'none'), (0, 0, 0))
        inc25 = a['income_now'] * 12 * self._cpi(2025) / self._cpi(Y)
        amt = lambda v: (v or 0) * self._cpi(2025) / self._cpi(Y)
        F = dict(age=age, age_to_60=age - 60, age_to_nps=age - nps, female=a['female'], married=a['married'], edu3=a['edu3'], hhsize=hh,
                 s_hhchg=hh - hh2, x_pension_recv=a['pension_recv'], x_retire_pension=a['retire_pension'], x_private_pension=a['private_pension'],
                 s_log_r=L[0], s_d1=L[0] - L[1], s_d2=L[0] - L[2], s_min3=ok.min() if len(ok) else np.nan,
                 s_vol3=ok.std() if len(ok) >= 2 else np.nan, employed=a['employed'], s_emp_l1=a.get('employed_1y'), s_emp_l2=a.get('employed_2y'),
                 s_lost=float(a.get('employed_2y') == 1 and a['employed'] == 0) if a.get('employed_2y') is not None else np.nan,
                 x_regular=reg, x_temp_daily=tmp, x_selfemp=slf, s_owner=a['owner'])
        for k, v in [('fin', amt(a.get('fin_asset'))), ('debt', amt(a.get('debt'))), ('real', amt(a.get('real_asset')))]:
            F[f's_{k}_r'] = float(np.clip(v / inc25, -50, 200)) if inc25 > 0 else np.nan
            F[f's_lg_{k}'] = float(np.sign(v) * np.log1p(abs(v)))
        if a.get('health') is not None: F['s_health'] = a['health']
        return F, r0

    def predict(self, a, income_year=None):
        F, r0 = self.features(a, income_year)
        age = F['age']
        if not (50 <= age <= 69):
            return dict(eligible=False, reason='모델은 50~69세에서만 검증됐어요.', ratio_now=r0)
        if not (r0 == r0 and r0 > 0):
            return dict(eligible=False, reason='지금 소득을 0보다 크게 적어야 풀이할 수 있어요.', ratio_now=r0)
        if r0 < 1:
            if self.b20 is None:
                return dict(eligible=False, reason='지금 소득이 기준선 아래라 이 모델의 대상이 아니에요.', ratio_now=r0)
            out = self.b20.run(F); out.update(eligible=True, mode='below', ratio_now=float(r0), model=self.b20.meta['model'])
            return out
        m = self.m21 if 's_health' in F else self.m20
        out = m.run(F); out.update(eligible=True, mode='above', ratio_now=float(r0), model=m.meta['model'])
        return out
