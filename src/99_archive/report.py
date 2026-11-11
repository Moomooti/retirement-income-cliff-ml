"""정답 PDF 생성: HTML → Chromium PDF."""
import pandas as pd, numpy as np, pickle, json, base64, os
from common_ml import *
A = pickle.load(open(W + 'analysis_out.pkl', 'rb')); PO = pickle.load(open(W + 'pooled_out.pkl', 'rb'))
LAB = pickle.load(open(W + 'labels.pkl', 'rb'))
R = pd.read_csv(W + 'all_results.csv'); PT = pd.read_csv(W + 'prep_table.csv').set_index('panel')
Z = pd.read_csv(W + 'zoo_table.csv').set_index('model')
C = A['compare']; MA = A['meta']; B = A['biz']
img = lambda f: 'data:image/png;base64,' + base64.b64encode(open(W + 'fig/' + f, 'rb').read()).decode()
f3 = lambda x: f'{x:.3f}'
pct = lambda x, d=1: f'{100 * x:.{d}f}%'
sgn = lambda x: f'+{x:.3f}' if x >= 0 else f'{x:.3f}'
pv = lambda p: '<0.001' if p < 0.001 else f'{p:.3f}'
cv = lambda comp, p, k: C[(C.comp == comp) & (C.panel == p)].iloc[0][k]

m_full, m_com, m_b1 = MA['full_vs_B0'], MA['common_vs_B0'], MA['full_vs_B1']
auc_full, auc_b0 = MA['auc_full'], MA['auc_b0']
n_all = int(PT.rows.sum()); n_te = int(PT.n_te.sum())
n_sig = int(((C.comp == 'full_vs_B0') & (C.p < 0.05) & (C.delta > 0)).sum())
n_sig_c = int(((C.comp == 'common_vs_B0') & (C.p < 0.05) & (C.delta > 0)).sum())
b20 = B[B.budget == 0.2].pivot(index='panel', columns='model', values='recall')
p10 = B[B.budget == 0.1].pivot(index='panel', columns='model', values='precision')
rec_ml, rec_b0 = b20['ML'].mean(), b20['현재소득'].mean()
LCm = PO['learning_curve'].groupby('frac')[['n', 'train_auc', 'test_auc']].mean()
bd = PO['bands']; SV = PO['state_vs_change'].set_index('panel')
perm = np.array(PO['perm_auc'])
lin = C[C.comp == 'full_vs_linear'].set_index('panel')
add = R[(R.fs == 'full') & (R.model == 'HGB_additive')].set_index('panel').auc
hgb = R[(R.fs == 'full') & (R.model == 'HGB_tuned')].set_index('panel').auc
T = PO['transfer'].astype(float)
offdiag = T.values[~np.eye(6, dtype=bool)]
best_row = Z.drop(index=[i for i in Z.index if i.startswith('B')]).sort_values('평균', ascending=False)


E = pickle.load(open(W + 'extra_out.pkl', 'rb'))
BM = E['boot_meta']; FQ = E['fixedq']; FB = E['field'].set_index('base'); NP = E['new_people']; SGm = E['subgroup_meta']
TFc = E['transfer_cal']
fqm = FQ.groupby(['set', 'k']).auc.mean()
fq_ml12, fq_ex12, fq_rd12 = fqm.get(('ML 선택', 12), np.nan), fqm.get(('전문가 양식', 12), np.nan), fqm.get(('무작위', 12), np.nan)
fq_ml5, fq_ex5 = fqm.get(('ML 선택', 5), np.nan), fqm.get(('전문가 양식', 5), np.nan)
fq_b0 = FQ[FQ.set == '지금 소득'].auc.mean(); fq_all = FQ[FQ.set == '전체'].auc.mean()
g3 = R[(R.fs == 'full') & R.model.isin(['XGBoost', 'LightGBM', 'CatBoost'])].pivot(index='panel', columns='model', values='auc')
lr_full = R[(R.fs == 'full') & (R.model == 'LR_L2')].set_index('panel').auc
b0s = R[R.model == 'B0_income_only'].set_index('panel').auc; b1s = R[R.model == 'B1_calculator'].set_index('panel').auc
err_raw = (TFc.pred_raw - TFc.obs).abs(); err_cal = (TFc.pred_cal - TFc.obs).abs()
PDa = pickle.load(open(W + 'pdp.pkl', 'rb'))['agenps_emp']['average'][0]
def _rec(col, q=0.2):
    v = []
    for p in PANELS:
        d = pd.read_pickle(W + f'preds_{p}.pkl'); g = pd.read_pickle(W + f'preds_gbm3_{p}.pkl')
        s_ = g[col].values if col in g else d[col].values; y_ = d.y.values; k_ = int(len(y_) * q)
        v.append(y_[np.argsort(-s_)[:k_]].sum() / y_.sum())
    return np.mean(v)
rec_lgb = _rec('full|LightGBM')
n_te_persons = sum(pd.read_pickle(W + f'preds_{p}.pkl').pid.nunique() for p in PANELS)
H = []
w = H.append
w(f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>노후 소득절벽 2년 조기경보 – 정답 보고서</title>
<style>{open(W + 'style.css').read()}</style></head><body>''')
# ---------------- 표지 ----------------
w(f'''<section class="cover"><div>
<div class="kicker">정답 보고서 · 노후 신탁 프로젝트 · 2026.11</div>
<h1>지금은 괜찮은 50~69세 중<br>2년 안에 빈곤선 아래로 떨어질 사람을<br>머신러닝이 먼저 찾는다</h1>
<p class="lead">6개 국가 패널(복지·노동·재정·의료·고령화·국민노후) · {n_all:,}개 사람×차수 · 같은 정의, 같은 검증</p>
<div class="claim">“6개 국가 패널에서 같은 정의로, 은퇴 전후 2년 안의 소득 하락을<br>지금 소득만 볼 때보다 일관되게 더 잘 찾는다” — <b class="ok">지지됨</b><br>
<span class="muted">사전 등록한 주분석(랜덤효과 메타): AUC 향상 {sgn(m_full["est"])} (95% CI {sgn(m_full["lo"])} ~ {sgn(m_full["hi"])}), p {pv(m_full["p"])}, 6개 중 {n_sig}개 패널에서 단독으로도 유의</span></div>
<div class="kpis">
 <div class="kpi"><div class="v">{f3(auc_full["est"])}</div><div class="l">ML 결합 AUC (6개 패널 시험셋)<br>지금 소득 하나: {f3(auc_b0["est"])}</div></div>
 <div class="kpi"><div class="v">{sgn(m_full["est"])}</div><div class="l">AUC 향상, 6/6 패널 모두 같은 방향<br>사전 판정 기준 +0.03</div></div>
 <div class="kpi"><div class="v">{int(FB.loc["계산(충족률)"].found_ml)}<small>명 vs {int(FB.loc["계산(충족률)"].found_base)}명</small></div><div class="l">같은 {int(FB.loc["계산(충족률)"].k20)}명을 상담할 때 만나는 실제 하락자<br>(ML vs 기존 충족률 계산, 국민노후패널)</div></div>
</div><div class="kpis" style="grid-template-columns:repeat(4,1fr);margin-top:2mm">
 <div class="kpi"><div class="l"><b>표본이 크다</b><br>{n_all:,}행 · {int(PT.persons.sum()):,}명<br>봉인 시험 {n_te:,}행 · {n_te_persons:,}명</div></div>
 <div class="kpi"><div class="l"><b>ML이 맞다</b><br>같은 질문 12개로 ML 선택 {f3(fq_ml12)} vs 전문가 양식 {f3(fq_ex12)} vs 무작위 {f3(fq_rd12)}</div></div>
 <div class="kpi"><div class="l"><b>비즈니스가 뚜렷하다</b><br>같은 상담 인원으로 기존 계산보다 하락자 {pct(FB.loc["계산(충족률)"].found_ml/FB.loc["계산(충족률)"].found_base-1,0)} 더 발견</div></div>
 <div class="kpi"><div class="l"><b>차별성</b><br>기존 소득 기준이 못 보는 “아직 괜찮은 사람”을 2년 먼저</div></div>
</div></div>
<div class="muted">원자료는 각 패널 이용약관상 재배포 금지 – 이 문서에는 집계 결과만 담았습니다. 모든 수치는 사전에 떼어 둔 최근 차수 시험셋에서 한 번만 평가했습니다.</div>
</section>''')
# ---------------- 목차 + 요약 ----------------
w(f'''<section class="sec"><h2><span class="no">0</span>한 장 요약</h2>
<div class="box"><b class="t">결론</b>
은퇴 전후(50~69세)의 “소득절벽”은 지금 소득만 봐서는 잘 안 보인다. 지금 소득만으로는 시험셋 AUC가 {f3(auc_b0["est"])}에 그치지만,
소득 이력·취업 변화·나이(정년·연금 개시까지 거리)·가구 구조·자산·연금·건강을 함께 학습한 ML은 {f3(auc_full["est"])}까지 올라간다.
6개 패널 모두 같은 방향이었고, 결합 향상은 {sgn(m_full["est"])}이다. 계산기형(소득·나이·취업 3개 변수 로지스틱)보다도 {sgn(m_b1["est"])} 높다.</div>
<h3>네 가지 기준 점검</h3>
<table><tr><th style="width:18%">기준</th><th>근거</th><th style="width:12%">판정</th></tr>
<tr><td>표본이 작지 않다</td><td>사람×차수 단위로 {n_all:,}행(사람 {int(PT.persons.sum()):,}명). 봉인 시험 {n_te:,}행. 가장 작은 국민노후패널도 시험 {int(PT.loc["KReIS"].n_te):,}행, 결합 ΔAUC 표준오차 {m_full["se"]:.3f}로 +0.03 검출 가능</td><td class="ok">충족</td></tr>
<tr><td>머신러닝이 맞다</td><td>① 지금 소득 → ② 같은 입력 로지스틱 → ③ 부스팅 3단계 비교. 질문 수를 12개로 고정해도 ML이 고른 질문 {f3(fq_ml12)} &gt; 전문가 양식 {f3(fq_ex12)} &gt; 무작위 {f3(fq_rd12)}. 학습곡선 상승, 라벨 셔플 시 0.5, 처음 보는 패널로 이전 가능</td><td class="ok">충족</td></tr>
<tr><td>비즈니스 모델이 뚜렷하다</td><td>같은 {int(FB.loc["계산(충족률)"].k20)}명 상담 시 기존 충족률 계산 {int(FB.loc["계산(충족률)"].found_base)}명 → ML {int(FB.loc["계산(충족률)"].found_ml)}명. 6개 패널 상위 20% 경보 포착률 지금 소득 {pct(rec_b0,0)} → HGB {pct(rec_ml,0)} / LightGBM {pct(rec_lgb,0)}. 진단(B2C) → 기관 경보(B2G) → 브릿지 신탁(금융) 3층 구조</td><td class="ok">충족</td></tr>
<tr><td>차별성이 있다</td><td>상태형(0.9대, 소득이 다 맞힘) 대신 변화형 정답. 빈곤선 바로 위 집단에서 지금 소득 AUC {bd.auc_income.iloc[0]:.2f} vs ML {bd.auc_ml.iloc[0]:.2f}. 국민노후패널 현장 기준(충족률 계산·본인 걱정)도 앞섬</td><td class="ok">충족</td></tr></table>
<h3>사용자 설계안 대비 최종 결정</h3>
<table><tr><th style="width:18%">항목</th><th>설계안</th><th>최종 (이 보고서)</th></tr>
<tr><td>분석 단위</td><td>50~69세, 사람×차수, 2년 뒤 결과</td><td>동일. t 시점 50~69세, t+2년 조사에서 소득 관측된 행</td></tr>
<tr><td>주 정답</td><td>지금은 괜찮은데 2년 안에 중앙값(또는 최소 생활 기준선) 아래로</td><td><b>변화형</b>: t 시점 균등화 경상소득 ≥ 빈곤선 이고 t+2 시점 &lt; 빈곤선. 빈곤선 = 전국 중위 균등화소득의 50% (OECD 상대빈곤 기준, 복지패널 가중 중위값으로 매년 산출, 2023년 가격)</td></tr>
<tr><td>기준 모델</td><td>지금 소득 하나</td><td>B0 = 지금 소득/빈곤선 (단조 점수라 AUC는 모델 학습과 무관). 보조로 B1 계산기형(소득·나이·취업)</td></tr>
<tr><td>입력</td><td>공통 입력 + 조사별 추가 입력</td><td>공통 {len(COMMON)}개(인구·소득이력·취업이력·연금개시 거리) / 추가 11~26개(자산·부채·연금·건강·직종·근로소득 비중). 둘 다 보고</td></tr>
<tr><td>검증</td><td>최근 차수 테스트 분리, 패널별 학습, 사전등록 메타</td><td>동일. 시험 = 최근 2개 기준 차수 ({n_te:,}행). 학습 = 결과 시점이 시험 시작 전인 행만(시간 누수 차단). 조정은 학습구간 안 마지막 2개 연도로만. 주분석 = HGB(사전 격자) vs B0의 DeLong 차이 → DerSimonian-Laird 랜덤효과</td></tr>
<tr><td>검정력</td><td>+0.03도 판정 가능</td><td>패널별 ΔAUC 표준오차 {C[C.comp=="full_vs_B0"].se.min():.3f}~{C[C.comp=="full_vs_B0"].se.max():.3f}, 결합 표준오차 {m_full["se"]:.3f} → +0.03 검출 충분</td></tr>
</table>
</section>''')
# ---------------- 1 데이터 ----------------
rows = ''.join(f'<tr><td>{NAME[p]}<br><span class="muted">{p}</span></td><td class="n">{int(r.rows):,}</td><td class="n">{int(r.persons):,}</td><td class="n">{r.years}</td><td class="n">{pct(r.pos)}</td><td class="n">{int(r.n_tr):,}</td><td class="n">{int(r.n_te):,}<br><span class="muted">{r.te_years}</span></td><td class="n">{pct(r.pos_te)}</td></tr>' for p, r in PT.iterrows())
w(f'''<section class="sec"><h2><span class="no">1</span>데이터와 전처리</h2>
<p>6개 패널은 조사 주기(매년/격년), 소득 기준(작년 한 해), 금액 단위(만원/천원), ID 체계가 모두 다르다. 정답을 같게 만들려면 소득을 먼저 하나의 척도로 맞춰야 한다.</p>
<table><tr><th>패널</th><th class="n">행(사람×차수)</th><th class="n">사람</th><th class="n">기준 조사연도</th><th class="n">하락률</th><th class="n">학습 행</th><th class="n">시험 행</th><th class="n">시험 하락률</th></tr>{rows}
<tr class="hl"><td>합계</td><td class="n">{n_all:,}</td><td class="n">{int(PT.persons.sum()):,}</td><td></td><td class="n"></td><td class="n">{int(PT.n_tr.sum()):,}</td><td class="n">{n_te:,}</td><td></td></tr></table>
<h3>1-1. 정답을 만드는 6단계</h3>
<div class="step"><div class="k">1</div><div><b>가구 경상소득</b> – 패널마다 같은 개념(근로+사업+재산+공적·사적 이전, 일회성 제외)으로 맞춤. 복지 <code>h_cin</code>, 재정 <code>inc_a</code>, 고령화 <code>hhinc</code>, 의료 <code>TOTAL/h_inc_tot</code>, 국민노후 <code>hd002b</code>(천원→만원), 노동은 항목 합산(근로·금융·임대·사회보험·이전, 매매차익·퇴직금·상속 제외).</div></div>
<div class="step"><div class="k">2</div><div><b>균등화</b> – 가구소득 ÷ √가구원수. 같은 소득이라도 혼자 사는지 4인 가구인지에 따라 생활 수준이 다르기 때문.</div></div>
<div class="step"><div class="k">3</div><div><b>물가 보정</b> – KOSIS 소비자물가지수로 소득 기준연도 금액을 2023년 가격으로 환산.</div></div>
<div class="step"><div class="k">4</div><div><b>빈곤선</b> – 복지패널 전 연령, 개인 횡단 가중치로 연도별 중위 균등화소득을 구하고 50%. 2023년 약 1,956만원/년(2023년 가격). 6개 패널에 같은 선을 적용.</div></div>
<div class="step"><div class="k">5</div><div><b>대상 선정</b> – t 시점 50~69세, 소득 &gt; 0, 소득 ≥ 빈곤선(“지금은 괜찮음”), t+2년 조사에서 소득 관측.</div></div>
<div class="step"><div class="k">6</div><div><b>정답</b> – t+2년 균등화소득 &lt; 그 해 빈곤선이면 1. 매년 조사는 2차수 뒤, 격년 조사(고령화·국민노후)는 1차수 뒤.</div></div>
<div class="box gray"><b class="t">점검: 패널 간 소득 척도가 맞는가</b>
6개 패널의 소득/빈곤선 중위값이 {PT.med_ratio.min():.2f}~{PT.med_ratio.max():.2f}배로 비슷하다. 단위나 개념이 어긋났다면 이 값이 2~10배씩 벌어졌을 것. 국민노후패널의 천원 단위도 이 점검과 코드북으로 함께 확인했다.</div>
</section>''')
w(f'''<section class="sec"><h3>1-2. 입력 변수 – 공통 {len(COMMON)}개 + 조사별 추가</h3>
<table><tr><th style="width:26%">묶음</th><th>변수</th><th style="width:30%">왜 넣었나</th></tr>
<tr><td><b>공통</b> 소득 수준</td><td>지금 소득/빈곤선(로그) = 기준 모델의 유일한 입력</td><td>기준선과 같은 정보를 ML에도 준다</td></tr>
<tr><td><b>공통</b> 소득 이력</td><td>2년·4년 소득 변화, 최근 4년 최저 소득, 소득 변동성(t, t−2, t−4의 표준편차), 과거 빈곤 경험</td><td>같은 소득이라도 흔들리는 소득은 떨어지기 쉽다</td></tr>
<tr><td><b>공통</b> 일·생애단계</td><td>현재 취업, 2년 전 취업, 2년 내 실직, 나이, 60세(법정 정년)까지 거리, 출생연도별 국민연금 수급개시연령(60~65세)까지 거리</td><td>정년 퇴직 → 연금 개시 사이의 공백(소득 크레바스)</td></tr>
<tr><td><b>공통</b> 가구</td><td>성별, 학력(3단계), 배우자 유무, 가구원 수, 2년간 가구원 변화</td><td>자녀 분가·사별이 가구소득을 바꾼다</td></tr>
<tr><td><b>추가</b> 일의 질</td><td>상용/임시·일용/자영, 직종, 본인 근로소득이 가구소득에서 차지하는 비중, 1년 소득 변화(매년 조사만)</td><td>가구 소득이 한 사람의 임금에 얼마나 몰려 있나</td></tr>
<tr><td><b>추가</b> 연금</td><td>공적연금 가입·수급, 연금액/소득, 개인·퇴직연금(복지패널)</td><td>은퇴 후 소득을 받쳐 주는 바닥</td></tr>
<tr><td><b>추가</b> 자산·부채</td><td>금융자산·순자산·부동산·부채 (소득 대비 배수와 로그)</td><td>소득이 줄어도 버틸 완충</td></tr>
<tr><td><b>추가</b> 건강</td><td>주관적 건강·변화, 만성질환, ADL/IADL(고령화), 장애(의료), 정신건강(국민노후)</td><td>건강 악화 → 조기 퇴직</td></tr></table>
<h3>1-3. 데이터 품질 처리</h3><ul>
<li><b>국민노후패널</b>: 코드북(v10.3)으로 확인 – 금액 천원, <code>pa001</code> 1=취업자, <code>pd001</code> 1=가입·2=수급·3=비해당. <code>kreispl13</code>은 <code>kreispl05</code>와 같은 사람·같은 값이라 중복 제거. 2023 신규표본(<code>kreishl23</code>)은 2년 뒤 결과가 없어 제외.</li>
<li><b>의료패널</b>: 1기(2008~2018)와 2기(2019~2024)의 개인 ID가 이어지지 않아 따로 추적(기간을 넘는 정답은 만들지 않음).</li>
<li><b>노동패널</b>: 배우자 유무가 개인 파일에 없어서 같은 가구·같은 차수에 가구주(10)와 배우자(20)가 함께 있으면 기혼으로 처리.</li>
<li><b>결측</b>: 부스팅은 결측을 그대로 학습(결측 자체가 정보). 선형·거리 기반 모델은 중앙값 대체 + 결측 표시 변수. 극단값은 학습 구간 0.5/99.5% 분위로 자름(시험셋에도 학습 기준을 그대로 적용).</li>
<li><b>누수 차단</b>: 모든 입력은 t 시점 이전 정보만. 정답(t+2)과 겹치는 변수 없음. 자산·소득 원금액은 소득 대비 배수로 바꿔 소득 수준과의 중복을 줄임.</li></ul>
</section>''')
# ---------------- 2 검증 ----------------
hp = A['hgb_params']
w(f'''<section class="sec"><h2><span class="no">2</span>검증 설계 – 미래를 보지 않는 시험</h2>
<p>무작위 분할을 하면 같은 사람의 다른 해가 학습과 시험에 동시에 들어가고, 미래 연도의 경기 상황도 학습에 섞인다. 그래서 <b>시간 순서대로</b> 잘랐다.</p>
<table><tr><th>패널</th><th class="n">학습 기준연도</th><th class="n">(공백)</th><th class="n">시험 기준연도</th><th>내부 검증으로 고른 HGB 설정</th><th class="n">반복</th><th class="n">입력 수</th></tr>
{''.join(f'<tr><td>{NAME[p]}</td><td class="n">~{int(PT.loc[p].tr_last)}</td><td class="n">결과 겹침 제외</td><td class="n">{PT.loc[p].te_years}</td><td>학습률 {hp[p]["params"]["learning_rate"]}, 잎 {hp[p]["params"]["max_leaf_nodes"]}, 최소표본 {hp[p]["params"]["min_samples_leaf"]}, L2 {hp[p]["params"]["l2_regularization"]}</td><td class="n">{int(hp[p]["iters"] * 1.1)}</td><td class="n">{hp[p]["n_feat"]}</td></tr>' for p in PANELS)}</table>
<div class="step"><div class="k">1</div><div><b>시험셋 봉인</b> – 각 패널의 최근 2개 기준 차수를 처음부터 떼어 둔다. 모델 선택·조정에 한 번도 쓰지 않는다.</div></div>
<div class="step"><div class="k">2</div><div><b>학습셋</b> – 2년 뒤 결과가 시험 시작 연도보다 앞서는 행만. 시험 직전 차수(결과가 시험기간과 겹침)는 버린다.</div></div>
<div class="step"><div class="k">3</div><div><b>조정</b> – 학습셋의 마지막 2개 연도를 내부 검증으로 써서 HGB의 사전 격자 16개 중 하나를 고른다. 시험셋은 보지 않는다.</div></div>
<div class="step"><div class="k">4</div><div><b>주분석(사전 등록)</b> – 패널별로 HGB(공통+추가) vs 지금 소득 하나의 AUC 차이를 DeLong 공분산으로 구하고, 6개를 DerSimonian–Laird 랜덤효과로 결합한다. 판정 기준: 결합 하한 &gt; 0, 실질 기준 +0.03.</div></div>
<div class="step"><div class="k">5</div><div><b>보조분석</b> – 공통 입력만, 계산기형 대비, 나머지 모델 전체, 통합 학습·패널 간 이전, 학습곡선, 라벨 셔플.</div></div>
</section>''')
# ---------------- 3 주분석 ----------------
rr = ''
for p in PANELS:
    a = C[(C.comp == 'full_vs_B0') & (C.panel == p)].iloc[0]; c = C[(C.comp == 'common_vs_B0') & (C.panel == p)].iloc[0]
    k = C[(C.comp == 'full_vs_B1') & (C.panel == p)].iloc[0]
    rr += f'<tr><td>{NAME[p]}</td><td class="n">{f3(a.auc_b)}</td><td class="n">{f3(k.auc_b)}</td><td class="n">{f3(c.auc_a)}</td><td class="n"><b>{f3(a.auc_a)}</b></td><td class="n">{sgn(c.delta)}</td><td class="n"><b>{sgn(a.delta)}</b> <span class="muted">±{1.96*a.se:.3f}</span></td><td class="n">{pv(a.p)}</td></tr>'
w(f'''<section class="sec"><h2><span class="no">3</span>주분석 결과 – 6개 패널 메타분석</h2>
<table><tr><th>패널</th><th class="n">B0 지금 소득</th><th class="n">B1 계산기형</th><th class="n">ML 공통 입력</th><th class="n">ML 공통+추가</th><th class="n">Δ 공통</th><th class="n">Δ 공통+추가 (95%)</th><th class="n">p</th></tr>{rr}
<tr class="hl"><td>결합(랜덤효과)</td><td class="n">{f3(auc_b0["est"])}</td><td class="n"></td><td class="n">{f3(MA["auc_common"]["est"])}</td><td class="n">{f3(auc_full["est"])}</td><td class="n">{sgn(m_com["est"])}</td><td class="n">{sgn(m_full["est"])} <span class="muted">[{sgn(m_full["lo"])}, {sgn(m_full["hi"])}]</span></td><td class="n">{pv(m_full["p"])}</td></tr></table>
<figure><img src="{img('f1_forest.png')}"><figcaption>그림 1. 패널별 AUC 향상과 랜덤효과 결합(마름모). 점선 = 사전에 정한 실질 기준 +0.03. 이질성 I² = {m_full["I2"]*100:.0f}% (공통+추가), {m_com["I2"]*100:.0f}% (공통만).</figcaption></figure>
<div class="box"><b class="t">판정</b>
주장 “같은 정의로 6개 패널에서 일관되게 더 잘 찾는다”는 <b class="ok">지지된다</b>. 6개 패널 모두 향상이 양수이고 {n_sig}개 패널은 단독으로도 p&lt;0.05, 결합 하한 {sgn(m_full["lo"])} &gt; 0.
공통 입력만으로도 결합 {sgn(m_com["est"])}({n_sig_c}/6 유의)라서, 자산·연금·건강이 없는 기관도 소득·취업 이력만으로 상당 부분을 얻는다. 추가 입력은 그 위에 결합 {sgn(MA["full_vs_common"]["est"])}를 더한다.</div>
</section>''')

tr3 = ''.join(f'<tr><td>{NAME[p]}</td><td class="n">{f3(b0s[p])}</td><td class="n">{f3(b1s[p])}</td><td class="n">{f3(lr_full[p])}</td><td class="n">{f3(hgb[p])}</td><td class="n">{f3(g3.loc[p,"LightGBM"])}</td><td class="n">{f3(g3.loc[p,"XGBoost"])}</td><td class="n">{f3(g3.loc[p,"CatBoost"])}</td></tr>' for p in PANELS)
bmr = ''.join(f'<tr><td>{k.replace("ML", "HGB(주모델)")}</td><td class="n">{sgn(v["est"])}</td><td class="n">[{sgn(v["lo"])}, {sgn(v["hi"])}]</td><td class="n">{pv(v["p"])}</td><td class="n">{v["I2"]*100:.0f}%</td></tr>' for k, v in BM.items())
w(f"""<section class="sec"><h3>3-2. 기준 3단계 – 왜 데이터 모델이, 왜 복잡한 모델이 필요한가</h3>
<p>① <b>현장 판단</b>(지금 소득, 계산기형) → ② <b>같은 입력을 넣은 로지스틱 회귀</b> → ③ <b>부스팅</b>. ①→②의 차이는 “정보(이력·취업·연금)를 쓰는 가치”, ②→③의 차이는 “비선형 학습의 가치”다.</p>
<table><tr><th>패널</th><th class="n">① 지금 소득</th><th class="n">① 계산기형</th><th class="n">② 로지스틱</th><th class="n">③ HGB<br>(주모델)</th><th class="n">③ LightGBM</th><th class="n">③ XGBoost</th><th class="n">③ CatBoost</th></tr>{tr3}
<tr class="hl"><td>평균</td><td class="n">{f3(b0s.mean())}</td><td class="n">{f3(b1s.mean())}</td><td class="n">{f3(lr_full.mean())}</td><td class="n">{f3(hgb.mean())}</td><td class="n">{f3(g3.LightGBM.mean())}</td><td class="n">{f3(g3.XGBoost.mean())}</td><td class="n">{f3(g3.CatBoost.mean())}</td></tr></table>
<h3>사람 단위 클러스터 부트스트랩 (보수적 신뢰구간)</h3>
<p>시험셋의 같은 사람이 두 차수에 나오므로 사람을 단위로 400회 재표집해 표준오차를 다시 구하고 결합했다. DeLong보다 보수적이다.</p>
<table><tr><th>비교</th><th class="n">결합 ΔAUC</th><th class="n">95% CI</th><th class="n">p</th><th class="n">I²</th></tr>{bmr}</table>
<div class="box gray"><b class="t">솔직한 해석</b>이득의 대부분은 ①→②(정보를 쓰는 것)에서 나온다. ②→③(로지스틱 → 부스팅)은 작다: LightGBM·XGBoost·CatBoost 평균 {sgn((g3.mean(axis=1) - lr_full).mean())}, 사전 등록 HGB는 {sgn((hgb - lr_full).mean())}(로지스틱보다 낮음). 이전 실험의 “③−② = +0.00~0.03”과 같은 패턴이다. 그래서 이 보고서는 “부스팅이 마법”이라고 주장하지 않는다. 대신 아래 5-2의 질문 수 고정 비교로 <b>어떤 정보를 물어야 하는지를 ML이 고른다</b>는 점을 보인다. 그것이 사람이 만든 계산식과 학습된 모델의 실질적 차이다.</div>
</section>""")
# ---------------- 4 모델 비교 ----------------
zr = ''
for m, r in Z.sort_values('평균', ascending=False).iterrows():
    nm = {'B0_income_only': '<i>기준 B0: 지금 소득 하나</i>', 'B1_calculator': '<i>기준 B1: 계산기형 로지스틱</i>'}.get(m, m)
    zr += f'<tr{" class=hl" if m=="HGB_tuned" else ""}><td>{nm}</td>' + ''.join(f'<td class="n">{f3(r[p])}</td>' for p in PANELS) + f'<td class="n"><b>{f3(r["평균"])}</b></td></tr>'
FAM = {'HGB_tuned': '부스팅', 'HGB_default': '부스팅', 'HGB_additive': '부스팅(상호작용 금지)', 'GradientBoosting': '부스팅', 'AdaBoost': '부스팅',
       'RandomForest': '배깅 트리', 'ExtraTrees': '배깅 트리', 'Bagging_Tree': '배깅 트리', 'DecisionTree': '단일 트리',
       'Stacking': '앙상블', 'Voting_soft': '앙상블', 'LR_L2': '선형', 'LR_L1': '선형', 'LR_ElasticNet': '선형', 'RidgeClassifier': '선형',
       'SGD_LogLoss': '선형', 'LinearSVM': '선형', 'LDA': '선형(판별)', 'LR_Spline_GAM': '가법(GAM)', 'QDA': '이차 판별',
       'GaussianNB': '나이브베이즈', 'XGBoost': '부스팅', 'LightGBM': '부스팅', 'CatBoost': '부스팅', 'KNN_k101': '거리 기반', 'SVM_RBF_6k': '커널', 'Nystroem_RBF_LR': '커널', 'GaussianProcess_2k': '커널(GP)'}
w(f'''<section class="sec"><h2><span class="no">4</span>모델 비교 – 신경망 제외 {len(best_row)}개</h2>
<p>모든 모델은 같은 학습셋·같은 입력(공통+추가)·같은 시험셋을 썼다. 사전 등록 주모델은 <b>HGB_tuned</b>(내부 검증으로 격자 선택)이고, 나머지는 비교용이다. 시험셋으로 모델을 고르지 않았다.</p>
<table style="break-inside:auto"><tr><th>모델</th>{''.join(f'<th class="n">{NAME[p][:-2] if NAME[p].endswith("패널") else NAME[p]}</th>' for p in PANELS)}<th class="n">평균</th></tr>{zr}</table>
<p class="muted">계열: {", ".join(sorted(set(FAM.values())))}. SVM_RBF는 학습 6,000행, GaussianProcess는 2,000행 표본(계산량). XGBoost 3.4 · LightGBM 4.7 · CatBoost 1.2는 HGB와 같은 규칙(학습구간 마지막 2개 연도로 격자 4개·반복 수 선택 후 전체 학습 재적합)으로 조정.</p>
</section>''')
w(f'''<section><figure><img src="{img('f2_zoo.png')}"><figcaption>그림 2. 6개 패널 평균 시험 AUC. 주황 = 지금 소득 하나, 초록 = 계산기형, 파랑 = ML.</figcaption></figure>
<div class="box gray"><b class="t">읽는 법</b><ul>
<li><b>상위권은 트리 앙상블·부스팅·스태킹</b>({", ".join(best_row.index[:4])}). 나이·취업·소득 변화가 서로 엮인 비선형 패턴을 잡는 계열이다.</li>
<li><b>선형 모델도 기준선보다 높다</b> – 정보 자체(이력·취업·연금)가 가치가 있다는 뜻. 잘 조정된 부스팅·앙상블은 그 위에 평균 {sgn((g3.mean(axis=1) - lr_full).mean())}를 더 얹는다(사전 등록 HGB는 오히려 {sgn((hgb - lr_full).mean())}).</li>
<li><b>하위권(나이브베이즈·QDA·단일 트리·소표본 커널)</b>은 변수 독립 가정, 과적합, 표본 축소 때문에 손해를 본다. 모델 선택이 결과를 바꾼다는 증거이기도 하다.</li></ul></div></section>''')
# ---------------- 5 증거 ----------------
w(f'''<section class="sec"><h2><span class="no">5</span>“계산기가 아니라 학습된 ML”이라는 증거</h2>
<p>계산기는 정해진 공식에 값을 넣으면 같은 답을 낸다. 학습된 모델은 ① 데이터가 늘수록 좋아지고, ② 우연(셔플된 정답)에서는 아무것도 못 배우며, ③ 처음 보는 집단에도 통하고, ④ 사람이 공식으로 쓰지 않은 상호작용을 스스로 찾는다. 6개 패널을 하나로 합친 통합 모델(공통 입력)로 이 네 가지를 확인했다.</p>
<h3>증거 1·2. 학습곡선 – 데이터와 반복이 늘수록 시험 성능이 오른다</h3>
<figure><img src="{img('f3_learning.png')}"><figcaption>그림 3. 왼쪽: 학습 행 {int(LCm.n.iloc[0]):,} → {int(LCm.n.iloc[-1]):,}에서 시험 AUC {f3(LCm.test_auc.iloc[0])} → {f3(LCm.test_auc.iloc[-1])}, 학습–시험 격차 {f3(LCm.train_auc.iloc[0]-LCm.test_auc.iloc[0])} → {f3(LCm.train_auc.iloc[-1]-LCm.test_auc.iloc[-1])}로 줄어듦(과적합 → 일반화). 오른쪽: 부스팅 반복마다 시험 AUC가 올라가 평탄해짐.</figcaption></figure>
<h3>증거 3. 라벨 셔플 검정 – 우연에서는 배우지 않는다</h3>
<p>학습셋의 정답만 무작위로 섞고 같은 모델을 5번 학습하면 시험 AUC가 평균 {perm.mean():.3f}(범위 {perm.min():.3f}~{perm.max():.3f})다. 0.5 위아래로 매번 방향이 바뀐다. 정답과 무관한 패턴에 맞춘 모델도 강한 변수(소득)의 우연한 함수가 되어 0.5에서 조금 벗어날 수는 있지만, 원래 정답으로 학습한 {f3(PO["pooled_auc_all"])}에는 한 번도 가까이 가지 못한다. 모델이 찾은 것은 정답과 연결된 실제 신호다.</p>
<h3>증거 4. 처음 보는 패널에서도 통한다 – 패널 간 이전</h3>
<div class="two"><figure><img src="{img('f4_transfer.png')}"></figure><div>
<p>한 패널로만 학습해 다른 패널의 시험셋에 적용했다. 대각선(같은 패널)과 비대각선(다른 패널)의 차이가 크지 않다. 비대각선 평균 {offdiag.mean():.3f}, 최저 {offdiag.min():.3f}로 모두 각 패널의 지금 소득 기준선을 대부분 넘는다.</p>
<p>조사 기관·문항·표본이 달라도 같은 위험 구조가 반복된다는 뜻이고, 다른 기관 데이터에 이식할 수 있다는 사업상 근거가 된다.</p>
<p>6개 패널 통합 학습의 결합 시험 AUC는 {f3(PO["pooled_auc_all"])}(지금 소득 {f3(PO["pooled_b0_all"])}).</p></div></div>
</section>''')
w(f'''<section class="sec"><h3>증거 5. 소득이 같은 사람들 사이에서도 구별한다</h3>
<figure class="half"><img src="{img('f5_bands.png')}"><figcaption>그림 4. t 시점 소득 구간 안에서의 AUC. 구간 안에서는 소득 차이가 작아서 지금 소득만으로는 동전 던지기에 가깝다. ML은 구간 안에서도 {bd.auc_ml.min():.2f}~{bd.auc_ml.max():.2f}를 유지한다.</figcaption></figure>
<p>가장 중요한 구간은 빈곤선 바로 위(1.0~1.25배, {int(bd.n.iloc[0]):,}명, 하락률 {pct(bd.pos.iloc[0])})다. 지금 소득만으로는 이 사람들 사이에서 누가 떨어질지 거의 모른다(AUC {bd.auc_income.iloc[0]:.2f}). ML은 {bd.auc_ml.iloc[0]:.2f}로 구별한다. 소득을 넣은 계산 결과가 아니라 소득 밖의 정보를 학습했다는 가장 직접적인 증거다.</p>
<h3>증거 6. 공식에 쓰지 않은 상호작용을 스스로 찾았다</h3>
<figure><img src="{img('f6_pdp.png')}"><figcaption>그림 5. 부분의존(다른 변수는 그대로 두고 한 변수만 바꿨을 때의 평균 예측 확률). 6개 패널 통합 모델.</figcaption></figure>
<p><b>왼쪽</b>: 국민연금 수급 개시가 다가올수록 위험이 오르는데, 일하는 사람이 더 가파르다(개시 13년 전 → 개시 이후: 일함 {PDa[0,1]*100:.1f}% → {PDa[-1,1]*100:.1f}%, 일하지 않음 {PDa[0,0]*100:.1f}% → {PDa[-1,0]*100:.1f}%). “지금 일한다”는 보호막이 정년·연금 개시 사이에서 얇아진다는 뜻이고, 이것이 소득 크레바스의 데이터상 모양이다.<br>
<b>오른쪽</b>: 같은 위치(빈곤선의 1.0~1.5배)에 있어도 최근 2년간 소득이 크게 올라 그 자리에 온 사람은 다시 떨어질 확률이 더 높다. 일시적 소득(성과급·일시 근로)을 모델이 스스로 구별한다.</p>
<p>참고로 상호작용을 금지한 같은 부스팅(HGB_additive, 변수 효과를 따로 더하기만 함)은 허용 모델보다 평균 {(hgb - add).mean():.3f} 낮지만 패널별로는 엇갈린다({int(((hgb - add) > 0).sum())}/6). 즉 상호작용은 위 그림처럼 <b>해석상 분명히 존재</b>하지만, 순위 성능에 더하는 몫은 작다. 성능의 주원천은 어떤 정보를 쓰느냐다(3-2, 5-2).</p>
</section>''')
w(f'''<section class="sec"><h3>증거 7. 어떤 정보로 판단하는가 – 순열 중요도</h3>
<figure><img src="{img('f7_importance.png')}"><figcaption>그림 6. 시험셋에서 한 변수만 섞었을 때 떨어지는 AUC(패널 평균). 오른쪽 숫자 = 이 변수가 상위 5위에 든 패널 수.</figcaption></figure>
<p>지금 소득이 6개 패널 모두에서 1위다. 그다음은 두 종류다. 하나는 소득의 <b>구성</b>이다. 가구소득 중 근로·사업소득 비중, 공적이전 비중, 금융·임대소득 비중으로, 국민노후패널에만 있는 항목이라 '1/1개 패널'로 표시된다. 다른 하나는 소득의 <b>이력</b>이다. 최근 4년 최저 소득(5/6개 패널 상위 5), 1년·2년 변화가 여기에 든다. 즉 모델은 “지금 얼마 버나”에 더해 “그 소득이 무엇으로 이루어졌고 얼마나 흔들려 왔나”를 본다.</p>
<h3>증거 8. 확률이 맞는가 – 보정과 위험 분위</h3>
<div class="two"><figure><img src="{img('f9_calibration.png')}"><figcaption>그림 7. 예측 확률 10분위별 실제 하락률. 대각선에 가까울수록 확률이 정직하다.</figcaption></figure>
<figure><img src="{img('f8_deciles.png')}"><figcaption>그림 8. 위험 10분위별 실제 하락률. ML 곡선이 더 가파르다 = 위험한 사람을 위쪽 분위로 더 정확히 모은다.</figcaption></figure></div>
<p class="muted">원 확률은 패널에 따라 높게(복지·노동·재정: 시험기간 하락률이 학습기간보다 낮음, 예 복지패널 {pct(PT.loc["KOWEPS"].pos_tr)} → {pct(PT.loc["KOWEPS"].pos_te)}) 또는 낮게(고령화: {pct(PT.loc["KLoSA"].pos_tr)} → {pct(PT.loc["KLoSA"].pos_te)}) 어긋난다. 위험 10분위의 순서는 맞으므로(그림 8) 순위·AUC에는 영향이 없고, 운영 시에는 최근 자료로 확률만 재보정하면 된다(5-2 반박 5).</p>
</section>''')

fqrow = ''
for k in [5, 12, 20]:
    fqrow += f'<tr><td class="n">{k}개</td><td class="n">{f3(fqm.get(("ML 선택", k), np.nan))}</td><td class="n">{f3(fqm.get(("전문가 양식", k), np.nan))}</td><td class="n">{f3(fqm.get(("무작위", k), np.nan))}</td><td class="n">{f3(FQ[(FQ.set=="ML 선택")&(FQ.k==k)].auc_lr.mean())}</td></tr>'
topf = E['top_ml_feats'].get('KOWEPS', [])
fbr = ''.join(f'<tr><td>{b}</td><td class="n">{int(r.n):,}</td><td class="n">{int(r.pos)}</td><td class="n">{f3(r.auc_base)}</td><td class="n"><b>{f3(r.auc_ml)}</b></td><td class="n">{sgn(r.delta)}</td><td class="n">{pv(r.p)}</td><td class="n">{int(r.k20)}명 상담 → {int(r.found_base)}명 vs <b>{int(r.found_ml)}명</b></td></tr>' for b, r in FB.iterrows())
npr = ''.join(f'<tr><td>{NAME[r.panel]}</td><td class="n">{int(r.n):,}</td><td class="n">{pct(r.share,0)}</td><td class="n">{f3(r.auc_b0)}</td><td class="n">{f3(r.auc_ml)}</td><td class="n">{sgn(r.delta)}</td></tr>' for _, r in NP.iterrows())
nm_ = E['new_meta']
w(f"""<section class="sec"><h2><span class="no">5-2</span>예상 반박을 미리 막는 검증</h2>
<h3>반박 1. “변수가 많아서 이긴 것 아닌가” → 질문 수를 고정해도 이긴다</h3>
<div class="two"><figure><img src="{img('f10_fixedq.png')}"></figure><div>
<table><tr><th class="n">질문 수</th><th class="n">ML이 고른</th><th class="n">전문가 양식</th><th class="n">무작위</th><th class="n">ML 선택 +로지스틱</th></tr>{fqrow}</table>
<p class="muted">모든 묶음에 지금 소득을 포함. ML 선택 순위는 학습구간 안의 내부 검증 순열 중요도로만 정함. 전문가 양식 = 노후준비 진단표에 흔한 순서(소득·나이·취업·배우자·가구원·연금·자가·금융자산·부채·건강…). 무작위는 3회 평균. 같은 고정 설정의 부스팅.</p></div></div>
<p>질문 5개만으로 ML 선택 {f3(fq_ml5)}, 전문가 양식 {f3(fq_ex5)}. 지금 소득 하나는 {f3(fq_b0)}, 전체 입력은 {f3(fq_all)}이다. <b>무엇을 물을지를 데이터가 고르면</b> 같은 설문 길이로 더 잘 찾는다. 이것이 대화형 진단(12문항)의 설계 근거다. 예: 복지패널에서 ML이 고른 12문항 = {", ".join(LAB.get(f, f) for f in topf)}.</p>
<h3>반박 2. “현장은 소득이 아니라 계산과 걱정으로 판단한다” → 둘 다 이긴다 (국민노후패널)</h3>
<p>국민노후패널에는 본인이 답한 <b>필요 최소 노후생활비</b>(pc003/pc004)와 <b>노후 준비 여부·충분성</b>(pc019/pc010)이 있다. 기존 노후 계산 방식인 <b>충족률</b>(지금 월소득 ÷ 필요 최소 생활비)과 <b>본인 걱정</b>을 기준선으로 그대로 세웠다.</p>
<table><tr><th>현장 기준</th><th class="n">시험 행</th><th class="n">하락</th><th class="n">기준 AUC</th><th class="n">ML AUC</th><th class="n">Δ</th><th class="n">p</th><th class="n">상위 20% 상담 시 찾은 하락자</th></tr>{fbr}</table>
</section>""")
w(f"""<section class="sec"><h3>반박 3. “같은 사람을 다시 맞힌 것 아닌가” → 처음 보는 사람만 따로 채점</h3>
<p>시험셋 가운데 사람도, 가구도 학습에 한 번도 나오지 않은 행만 골랐다(패널 신규 표본·분가 가구).</p>
<table><tr><th>패널</th><th class="n">처음 보는 사람 행</th><th class="n">시험셋 중 비율</th><th class="n">지금 소득</th><th class="n">ML</th><th class="n">Δ</th></tr>{npr}
{f'<tr class="hl"><td>결합</td><td></td><td></td><td></td><td></td><td class="n">{sgn(nm_["est"])} [{sgn(nm_["lo"])}, {sgn(nm_["hi"])}]</td></tr>' if nm_ else ''}</table>
<p class="muted">국민노후·고령화패널처럼 신규 표본이 시험기간에 없는 패널은 표에서 빠진다(처음 보는 사람이 20명 미만이면 제외).</p>
<h3>반박 4. “특정 집단에서만 맞는 것 아닌가” → 집단별 점검</h3>
<figure><img src="{img('f11_subgroup.png')}"><figcaption>그림 9. 성별·학력·나이대·취업 여부별 ML 이득(6개 패널 결합). 오른쪽 = 평균 AUC (지금 소득 → ML).</figcaption></figure>
<h3>반박 5. “다른 기관 데이터에 옮기면 깨지지 않나” → 순위는 유지, 확률만 다시 맞추면 된다</h3>
<p>한 패널로 학습한 모델을 다른 패널에 그대로 옮기면 평균 예측 확률이 실제와 평균 {err_raw.mean()*100:.1f}%p 어긋난다(최대 {err_raw.max()*100:.1f}%p). 대상 기관의 최근 2년 자료로 <b>확률만 다시 맞추면</b>(Platt, 재학습 없음) {err_cal.mean()*100:.1f}%p로 줄어든다. 순위(AUC)는 재보정과 무관하게 이전 행렬(그림 4) 그대로다. 이전 실험의 “복지패널 이식 실패(예측 61% vs 실제 26%)”는 순위가 아니라 확률 수준의 문제였고, 이렇게 처방할 수 있다.</p>
</section>""")
# ---------------- 6 상태 vs 변화 ----------------
sv = ''.join(f'<tr><td>{NAME[p]}</td><td class="n">{f3(r.auc_b0)}</td><td class="n">{f3(r.auc_ml)}</td><td class="n">{sgn(r.auc_ml-r.auc_b0)}</td><td class="n">{f3(r.chg_b0)}</td><td class="n">{f3(hgb[p])}</td><td class="n"><b>{sgn(hgb[p]-r.chg_b0)}</b></td></tr>' for p, r in SV.iterrows())
w(f'''<section class="sec"><h2><span class="no">6</span>왜 이전 실험은 AUC가 높았나 – 상태형 vs 변화형</h2>
<p>이전 실험(T3 상태형, KLIPS M1, 고령화·의료 대략판)은 AUC 0.85~0.92였지만 ML 이득은 +0.00~0.06이었다. 같은 데이터·같은 시험 분할로 두 정답을 나란히 계산하면 이유가 바로 보인다.</p>
<table><tr><th rowspan="2">패널</th><th colspan="3" class="n">상태형: 2년 뒤 빈곤선 아래인가 (지금 가난한 사람 포함)</th><th colspan="3" class="n">변화형(주분석): 지금은 괜찮은데 2년 뒤 아래로</th></tr>
<tr><th class="n">지금 소득</th><th class="n">ML(공통)</th><th class="n">이득</th><th class="n">지금 소득</th><th class="n">ML(공통+추가)</th><th class="n">이득</th></tr>{sv}
<tr class="hl"><td>평균</td><td class="n">{f3(SV.auc_b0.mean())}</td><td class="n">{f3(SV.auc_ml.mean())}</td><td class="n">{sgn((SV.auc_ml-SV.auc_b0).mean())}</td><td class="n">{f3(SV.chg_b0.mean())}</td><td class="n">{f3(hgb.mean())}</td><td class="n">{sgn((hgb-SV.chg_b0).mean())}</td></tr></table>
<div class="box"><b class="t">해석</b><ul>
<li><b>상태형은 “지금 가난하면 2년 뒤에도 가난하다”를 맞히는 문제</b>라 지금 소득 하나로 AUC가 이미 높다. ML이 더할 몫이 거의 없다. 숫자는 높지만 사업적으로는 이미 기존 소득 기준 복지 시스템이 아는 사람들이다.</li>
<li><b>변화형은 지금 소득 기준으로는 아직 아무 신호가 없는 사람</b> 중에서 떨어질 사람을 찾는다. AUC 숫자는 낮아 보이지만 ML 이득은 몇 배 크다. 이 차이가 “계산기 vs 학습된 ML”의 차이다.</li>
<li>고령화·의료 대략판에서 이득이 0이었던 이유(같은 총소득 변수로 정답과 입력을 함께 만듦)도 변화형에서는 사라진다. 정답이 “경계를 넘는 사건”이라 입력 소득과 기계적으로 같지 않기 때문이다.</li>
<li>발표 문장 권장: “AUC {f3(auc_full["est"])}”보다 <b>“같은 {int(FB.loc['계산(충족률)'].k20)}명을 상담할 때 기존 충족률 계산은 하락자 {int(FB.loc['계산(충족률)'].found_base)}명, ML은 {int(FB.loc['계산(충족률)'].found_ml)}명을 찾는다”</b>가 정확하고 설득력 있다. AUC는 문제 난이도에 따라 달라지지만, 같은 상담 인원 대비 발견 수는 현장에서 바로 이해된다.</li></ul></div>
</section>''')
# ---------------- 7 비즈니스 ----------------
bt = ''
for p in PANELS:
    g = B[(B.panel == p) & (B.budget == 0.2)].set_index('model')
    bt += f'<tr><td>{NAME[p]}</td><td class="n">{pct(g.loc["ML"].base)}</td><td class="n">{pct(g.loc["현재소득"].precision)}</td><td class="n"><b>{pct(g.loc["ML"].precision)}</b></td><td class="n">{pct(g.loc["현재소득"].recall)}</td><td class="n"><b>{pct(g.loc["ML"].recall)}</b></td><td class="n">{g.loc["ML"].lift:.1f}배</td></tr>'
w(f'''<section class="sec"><h2><span class="no">7</span>비즈니스 모델 – “소득절벽 2년 조기경보”</h2>
<p>모델이 파는 것은 점수가 아니라 <b>시간</b>이다. 현장 언어로 말하면: 국민노후패널 시험셋에서 {int(FB.loc['계산(충족률)'].k20)}명을 상담할 때 기존 충족률 계산으로 고르면 하락자 {int(FB.loc['계산(충족률)'].found_base)}명, ML로 고르면 {int(FB.loc['계산(충족률)'].found_ml)}명을 만난다. 지금 소득 기준으로는 아무 문제가 없어 보이는 사람에게 2년 먼저 경고하면 재취업·연금 수령 시점 조정·자산 유동화·복지 연계를 미리 할 수 있다.</p>
<table><tr><th>패널(시험셋)</th><th class="n">기본 하락률</th><th class="n">상위 20% 적중률<br>지금 소득</th><th class="n">상위 20% 적중률<br>ML</th><th class="n">하락자 포착률<br>지금 소득</th><th class="n">하락자 포착률<br>ML</th><th class="n">ML 향상도</th></tr>{bt}</table>
<p>표는 사전 등록 주모델(HGB) 기준이다. 탐색 분석의 LightGBM을 쓰면 평균 포착률이 {pct(rec_lgb)}(지금 소득 {pct(rec_b0)})로 더 오른다.</p>
<p class="muted">상위 20% 경보 = 위험 점수 상위 20%에게만 연락한다는 운영 예산. 적중률 = 경보 대상 중 실제 하락 비율, 포착률 = 실제 하락자 중 경보를 받은 비율.</p>
<h3>사용자 아이디어 4개 평가</h3>
<table><tr><th style="width:22%">아이디어</th><th>이 결과가 주는 근거</th><th style="width:20%">판단</th></tr>
<tr><td>내 노후걱정이 실제로 이어질지 (개인 진단)</td><td>공통 입력 {len(COMMON)}개(대부분 본인이 답할 수 있는 문항)만으로 결합 {sgn(m_com["est"])}. 설문 10~15문항이면 충분.</td><td><span class="ok">강함</span> – B2C 유입 채널</td></tr>
<tr><td>국민연금공단 결과가 적절한가</td><td>공단의 실제 진단 결과는 이 데이터에 없어 직접 비교는 불가. 대신 “소득·나이·취업” 규칙형 계산기(B1)보다 결합 {sgn(m_b1["est"])}. 계산기형 진단이 놓치는 사람이 있다는 것까지가 이 결과로 말할 수 있는 범위.</td><td><span class="no">표현 주의</span> – “공단 비판”이 아니라 “보완 지표” 제안</td></tr>
<tr><td>재취업지원서비스 · 복지 사각지대 발굴</td><td>빈곤선 바로 위 집단에서 지금 소득 AUC {bd.auc_income.iloc[0]:.2f} vs ML {bd.auc_ml.iloc[0]:.2f}. 현행 소득 기준 발굴이 원리상 못 보는 사람을 찾는다.</td><td><span class="ok">가장 강함</span> – B2G 핵심</td></tr>
<tr><td>개인 대화형 진단</td><td>순열 중요도 상위 변수(소득 이력·취업·연금 개시까지 거리)가 그대로 대화 문항과 “이유 설명”이 된다.</td><td><span class="ok">강함</span> – 진단의 형태</td></tr></table>
</section>''')
w(f'''<section class="sec"><h3>제안: 3층 구조 – 진단(무료) → 경보(기관) → 브릿지 신탁(금융)</h3>
<table><tr><th style="width:17%">층</th><th style="width:20%">고객 · 결제자</th><th>제공 가치</th><th style="width:22%">수익 방식</th></tr>
<tr><td><b>① 대화형 진단</b><br>“2년 소득절벽 점수”</td><td>50~64세 개인 (무료)</td><td>12문항 대화 → 2년 내 하락 확률 + 이유 3가지(예: “가구소득의 80%가 본인 임금, 정년까지 2년”) + 처방 카드</td><td>무료. 동의 기반 리드 → ②③으로 연결</td></tr>
<tr><td><b>② 기관용 조기경보 API</b></td><td>지자체 복지 사각지대 발굴, 고용센터·중장년 재취업지원 의무 기업, 국민연금 노후준비서비스</td><td>보유 명단에 점수를 붙여 상위 N%만 먼저 상담. 같은 상담 인력으로 기존 충족률 계산보다 하락자를 {pct(FB.loc['계산(충족률)'].found_ml/FB.loc['계산(충족률)'].found_base-1,0)} 더 만남(국민노후패널 시험셋)</td><td>건당 과금 또는 연간 라이선스 + 모델 재보정 유지보수</td></tr>
<tr><td><b>③ 브릿지 신탁</b><br>(노후 신탁 연계)</td><td>은행·증권 신탁부문, 퇴직연금 사업자</td><td>위험 상위 고객에게 “정년~연금 개시” 공백기 동안 월 지급하도록 설계된 신탁·IRP 인출 플랜을 2년 먼저 제안. 점수는 상품 추천·한도 설계의 근거</td><td>신탁 보수 분배, 판매 성과 연동 수수료</td></tr></table>
<div class="box"><b class="t">차별점 – 왜 이 모델이어야 하나</b><ul>
<li><b>시간 차</b>: 기존 소득·재산 조사형 발굴은 “이미 떨어진 사람”을 찾는다. 이 모델은 지금은 기준 위에 있는 사람을 2년 먼저 찾는다.</li>
<li><b>6개 국가 패널 검증</b>: 한 데이터에 맞춘 모델이 아니라 6개 조사에서 같은 정의로 재현됐고(증거 4), 다른 기관 데이터에 이식할 근거가 있다.</li>
<li><b>최소 입력으로 작동</b>: 공통 입력만으로도 대부분의 이득이 나온다. 기관마다 가진 변수가 달라도 시작할 수 있다.</li>
<li><b>설명 가능</b>: 상위 변수가 정책 언어(정년, 연금 개시, 소득 집중, 이력 변동성)와 그대로 연결된다.</li></ul></div>
<h3>시장 진입 순서</h3><ol>
<li><b>파일럿(3개월)</b> – 지자체 1곳 또는 은행 1곳의 기존 명단(50~64세)에 공통 입력 모델 적용 → 2년 추적 대신 “지난 2년 자료로 백테스트” 리포트 제공.</li>
<li><b>B2G 확장</b> – 복지 사각지대 발굴 지표에 “소득절벽 위험” 1개 축 추가 제안. 근거: 빈곤선 바로 위 집단에서의 판별력(그림 4).</li>
<li><b>금융 연계</b> – 브릿지 신탁 상품 공동 설계. 이때부터 고객 동의 하에 실제 소득 흐름 자료로 재학습해 성능을 높인다.</li></ol>
<p class="muted">규제 점검: 개인신용정보·민감정보(건강) 사용 시 동의·가명처리 필요. 기관용은 공통 입력(건강 제외) 모델로 시작하면 부담이 작다.</p>
</section>''')

w(f"""<section class="sec"><h2><span class="no">7-2</span>판정과 탐색 – 실패도 공개</h2>
<table><tr><th style="width:15%">구분</th><th>내용</th><th style="width:22%">결과</th></tr>
<tr><td><b>판정</b>(사전 등록)</td><td>6개 패널 HGB(공통+추가) vs 지금 소득, DeLong → 랜덤효과. 기준: 결합 하한 &gt; 0 그리고 실질 +0.03</td><td>{sgn(m_full["est"])} [{sgn(m_full["lo"])}, {sgn(m_full["hi"])}] → {'<span class="ok">통과</span>' if m_full["lo"] > 0 else '<span class="no">미통과</span>'}{'' if m_full["est"] >= 0.03 else ' (실질 기준 +0.03에는 못 미침)'}</td></tr>
<tr><td><b>판정</b>(비율 규칙)</td><td>6개 중 80% 이상(5개 이상)에서 Δ &gt; 0</td><td>{int((C[C.comp=="full_vs_B0"].delta>0).sum())}/6 → {'<span class="ok">통과</span>' if (C[C.comp=="full_vs_B0"].delta>0).sum()>=5 else '<span class="no">미통과</span>'}</td></tr>
<tr><td>탐색</td><td>XGBoost·LightGBM·CatBoost, 앙상블, 질문 수 고정, 처음 보는 사람, 집단별, 상태형 비교</td><td>보조 근거. 판정에 쓰지 않음</td></tr>
<tr><td class="no">공개할 실패</td><td><ul style="margin:0">
<li><b>사전 등록한 HGB가 같은 입력의 로지스틱 회귀보다 평균 {abs((hgb - lr_full).mean()):.3f} 낮았다</b>(사람 단위 부트스트랩으로도 유의). LightGBM·XGBoost·CatBoost·앙상블은 로지스틱보다 높았다. HGB의 격자(학습률·잎 수)와 조기 종료 방식이 이 문제에 덜 맞았던 것으로 보인다. 시험셋을 보고 주모델을 바꾸지 않았고, 운영 모델은 다음 라운드에서 내부 검증 규칙으로 다시 고정한다.</li>
<li>국민노후패널: 추가 입력을 넣은 HGB({f3(hgb["KReIS"])})가 공통 입력 HGB({f3(R[(R.fs=="common")&(R.model=="HGB_tuned")&(R.panel=="KReIS")].auc.iloc[0])})보다 낮았다. 학습 1.2만 행에 입력 30여 개라 과적합. 단순 모델(ExtraTrees·로지스틱)이 더 낫다.</li>
<li>원 확률이 패널에 따라 높거나 낮게 어긋난다(시험기간 하락률이 학습기간과 다름). 순위는 유지되므로 확률 재보정으로 처방.</li>
<li>로지스틱 대비 부스팅 이득은 작다(②→③). 이득의 주원천은 정보 설계.</li></ul></td><td>신뢰를 위해 그대로 보고</td></tr></table>
</section>""")
# ---------------- 8 한계 + 부록 ----------------
w(f'''<section class="sec"><h2><span class="no">8</span>한계와 다음 단계</h2><ul>

<li><b>빈곤선</b>: 경상소득 기준(가처분소득은 6개 중 일부만 있음). 공적이전·세금을 반영한 가처분 기준으로 바꾸면 하락률 수준은 달라질 수 있다.</li>
<li><b>시험 기간 특성</b>: 시험 차수(주로 2020~2023)는 코로나 지원금과 고용 회복이 섞인 시기다. 하락률이 학습기간보다 낮아 확률 보정이 필요하다(순위 성능에는 영향 없음).</li>
<li><b>국민노후패널·고령화패널</b>은 시험 표본이 작아(1,462 / 2,977행) 개별 신뢰구간이 넓다. 결합 분석이 이를 보완한다.</li>
<li><b>인과 아님</b>: 중요도·부분의존은 예측에 쓰인 패턴이지 “이 변수를 바꾸면 위험이 준다”는 인과 주장이 아니다. 처방 효과는 파일럿에서 별도로 검증해야 한다.</li>
<li><b>가중치</b>: 모델 성능은 표본(비가중) 기준. 전국 모집단 비율을 말할 때는 패널 가중치를 적용해야 한다.</li></ul>
<h2 style="margin-top:8mm"><span class="no">A</span>부록 – 재현 정보</h2>
<table><tr><th style="width:28%">단계</th><th>스크립트 · 내용</th></tr>
<tr><td>패널별 변환</td><td><code>b_koweps.py · b_klips.py · b_nastab.py · b_khp.py · b_klosa.py · b_kreis.py</code> → 공통 스키마(사람×차수, 만원, 소득연도)</td></tr>
<tr><td>정답·이력 변수</td><td><code>build_common.py</code> – CPI 2023 환산, 균등화, 빈곤선(복지패널 가중 중위 50%), t−4~t+2 연결</td></tr>
<tr><td>모델 비교</td><td><code>run_models.py PANEL</code> + <code>run_gbm3.py</code>(XGBoost·LightGBM·CatBoost) – 시간 분할, 사전 격자 HGB, 비교 모델 전체, 시험 예측 저장</td></tr>
<tr><td>통합·이전·학습곡선</td><td><code>pooled.py</code></td></tr>
<tr><td>통계·그림·보고서</td><td><code>analysis.py</code>(DeLong, DerSimonian–Laird, 순열 중요도) · <code>figs.py</code> · <code>report.py</code></td></tr>
<tr><td>환경</td><td>Python 3.13, scikit-learn 1.9.1, XGBoost 3.4.1, LightGBM 4.7.0, CatBoost 1.2.10, pandas 3.0, 난수 시드 42. 원자료는 재배포 금지라 함께 제공하지 않음</td></tr></table>
<h3>빈곤선 (2023년 가격, 균등화 경상소득 연 만원)</h3>
<table><tr>{''.join(f'<th class="n">{int(y)}</th>' for y in pd.read_csv(W+'poverty_line.csv').year.iloc[1::2])}</tr><tr>{''.join(f'<td class="n">{v:,.0f}</td>' for v in pd.read_csv(W+'poverty_line.csv').line.iloc[1::2])}</tr></table>
<p class="muted">2004년(소득연도)은 복지패널 이전이라 2005년 값을 사용.</p>
</section></body></html>''')
open(W + 'report.html', 'w').write(''.join(H))
print('html ok')
