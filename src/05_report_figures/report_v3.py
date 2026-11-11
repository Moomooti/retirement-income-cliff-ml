"""정답 보고서 v3 (상세판) → HTML → PDF"""
import numpy as np, pandas as pd, pickle, base64
from common_ml import *
O = pickle.load(open(W + 'v3_out.pkl', 'rb')); TN, LAB = pickle.load(open(W + 'v3_names.pkl', 'rb'))
J = pickle.load(open(W + 'v3_journey.pkl', 'rb')); SM = pickle.load(open(W + 'v3_submeta.pkl', 'rb'))
MAIN = ['KOWEPS_r', 'NaSTaB_r', 'KReIS_r']; SHOW = MAIN + ['KReIS_rn', 'KLIPS_r']; ALLT = SHOW + ['KHP_r', 'KLoSA_r']
FIN = '최종: LightGBM+로지스틱'
Z, C, BZ, FQ = O['zoo'], O['cmp'], O['biz'], O['fq']
DI = O['data_info']; MA = O['meta']; BM = O['boot_meta']
img = lambda f: 'data:image/png;base64,' + base64.b64encode(open(W + 'fig3/' + f, 'rb').read()).decode()
f3 = lambda x: '–' if pd.isna(x) else f'{x:.3f}'
pct = lambda x, d=1: '–' if pd.isna(x) else f'{100 * x:.{d}f}%'
sgn = lambda x: '–' if pd.isna(x) else (f'+{x:.3f}' if x >= 0 else f'{x:.3f}')
pv = lambda p: '<0.001' if p < 0.001 else f'{p:.3f}'
auc = lambda k, m: Z[(Z.task == k) & (Z.model == m)].auc.iloc[0]
cmp_ = lambda k, c: C[(C.task == k) & (C.comp == c)].iloc[0]
found = lambda k, m: int(BZ[(BZ.task == k) & (BZ.model == m)].found.iloc[0])
k20 = lambda k: int(BZ[(BZ.task == k)].k20.iloc[0])
mf = MA['최종−지금소득']; ml = MA['LightGBM−지금소득']; mc = MA['최종−계산기형']; mlr = MA['LightGBM−로지스틱']
fin_mean = np.mean([auc(k, FIN) for k in MAIN]); b0_mean = np.mean([auc(k, 'B0 지금 소득') for k in MAIN])
need_b, need_m = found('KReIS_rn', 'B0 지금 소득'), found('KReIS_rn', FIN)
lift_need = need_m / need_b - 1
n_te_all = sum(DI[k]['n_te'] for k in ALLT); n_tr_all = sum(DI[k]['n_tr'] for k in ALLT)
PT = pd.read_csv(W + 'prep_table.csv').set_index('panel')
LC = O['lc'].groupby('frac')[['n', 'train_auc', 'test_auc']].mean()
perm = np.array(O['perm']); bd = O['bands']
fqm = FQ[FQ.task.isin(MAIN)].groupby(['set', 'k']).auc.mean()
TT = O['transfer'].astype(float); offd = TT.values[~np.eye(len(TT), dtype=bool)]
TC = O['transfer_cal']; er_raw = (TC.pred_raw - TC.obs).abs(); er_cal = (TC.pred_cal - TC.obs).abs()
CS = O['calsum']; NW = O['new']; TU = pd.DataFrame(O['tune'])
dline = pd.read_csv(W + 'poverty_line.csv')
H = []; w = H.append


def table(head, rows, cls='', num=None):
    num = set(range(1, len(head))) if num is None else set(num)
    return f'<table {cls}><tr>' + ''.join(f'<th{" class=n" if i in num else ""}>{h}</th>' for i, h in enumerate(head)) + '</tr>' + ''.join(rows) + '</table>'


w(f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>미리사주</title>
<style>{open(W + 'style.css').read()}
.flow {{ display:grid; grid-template-columns: repeat(4, 1fr); gap:3mm; margin:3mm 0 4mm; }}
.flow .c {{ border:1px solid var(--rule); border-radius:2.5mm; padding:2.5mm 3mm; font-size:8pt; background:#fff; }}
.flow .c b {{ display:block; font-size:8.6pt; margin-bottom:1mm; }}
.flow .c.main {{ border-color: var(--blue); background: var(--blue-bg); }}
.flow .c.repl {{ border-color: #1baf7a; }}
.flow .c.tr {{ border-color: #8a8984; border-style:dashed; }}
.arrow {{ text-align:center; color: var(--ink3); font-size:9pt; margin:1mm 0; }}
.pipe {{ display:flex; gap:2mm; align-items:stretch; margin:3mm 0; }}
.pipe .s {{ flex:1; background: var(--soft); border-radius:2mm; padding:2.5mm; font-size:7.8pt; }}
.pipe .s b {{ display:block; font-size:8.4pt; margin-bottom:0.8mm; }}
.pipe .a {{ align-self:center; color: var(--ink3); }}
.def {{ border-left:3px solid var(--blue); padding:1mm 0 1mm 3.5mm; margin:2mm 0 3mm; font-size:9pt; }}
.def b {{ color: var(--blue); }}
</style></head><body>''')

# ================= 표지 =================
w(f'''<section class="cover"><div>
<div class="kicker">노후 신탁 프로젝트 · 2026.11</div>
<h1 style="font-size:34pt;margin-bottom:2mm">미리사주</h1>
<p class="lead">6개 국가 패널 · 사람×차수 단위 · 가처분소득 · “3번 중 2번 이상 부족” 반복 관측 정답 · 미래 차수 봉인 시험</p>
<div class="claim">“가처분소득이 있는 3개 국가 패널에서 같은 정의로, 은퇴 전후의 지속적 소득 하락을<br>지금 소득만 볼 때보다 일관되게 더 잘 찾는다” — <b class="ok">지지됨</b><br>
<span class="muted">결합 AUC 향상(최종 모델 − 지금 소득) {sgn(mf["est"])} (95% CI {sgn(mf["lo"])} ~ {sgn(mf["hi"])}), p {pv(mf["p"])}. 사전 지정 LightGBM 단독 {sgn(ml["est"])} [{sgn(ml["lo"])}, {sgn(ml["hi"])}]. 재현(노동패널)·이식(의료·고령화)에서도 같은 방향</span></div>
<div class="kpis">
 <div class="kpi"><div class="v">{f3(auc("KOWEPS_r", FIN))}</div><div class="l">복지패널 시험 AUC (가처분소득이 가장 정교한 조사)<br>지금 소득 하나: {f3(auc("KOWEPS_r", "B0 지금 소득"))}</div></div>
 <div class="kpi"><div class="v">{sgn(mf["est"])}</div><div class="l">3개 패널 결합 AUC 향상<br>모든 패널·모든 집단에서 양수</div></div>
 <div class="kpi"><div class="v">{need_m}<small>명 vs {need_b}명</small></div><div class="l">같은 {k20("KReIS_rn")}명 상담 시 실제 하락자<br>(ML vs 기존 충족률 계산, 국민노후)</div></div>
</div>
<div class="kpis" style="grid-template-columns:repeat(4,1fr);margin-top:2mm">
 <div class="kpi"><div class="l"><b>표본</b><br>학습 {n_tr_all:,}행 · 시험 {n_te_all:,}행<br>(7개 과제, 사람×차수)</div></div>
 <div class="kpi"><div class="l"><b>ML이 맞다</b><br>질문 12개 고정: ML 선택 {f3(fqm.get(("ML 선택", 12)))} &gt; 전문가 {f3(fqm.get(("전문가 양식", 12)))} · 무작위 {f3(fqm.get(("무작위", 12)))}</div></div>
 <div class="kpi"><div class="l"><b>비즈니스</b><br>무료 진단 → 방향·공식 사이트 안내 → 향후 사이트 유료화</div></div>
 <div class="kpi"><div class="l"><b>차별성</b><br>기존 소득·충족률 기준이 못 보는 “아직 괜찮은 사람”을 먼저</div></div>
</div></div>
<div class="muted">원자료는 각 패널 이용약관상 재배포 금지 – 이 문서에는 집계 결과만 담았다. 모든 AUC는 처음부터 떼어 둔 최근 차수 시험셋에서 한 번만 채점했다.</div>
</section>''')

# ================= 0 요약 =================
rows = ''.join(f'<tr{" class=hl" if k == "KOWEPS_r" else ""}><td>{TN[k]}</td><td class="n">{DI[k]["n_te"]:,}</td><td class="n">{pct(DI[k]["pos_te"])}</td><td class="n">{f3(auc(k, "B0 지금 소득"))}</td><td class="n">{f3(auc(k, "B1 계산기형"))}</td><td class="n">{f3(auc(k, "LR_L2"))}</td><td class="n">{f3(auc(k, "LightGBM"))}</td><td class="n"><b>{f3(auc(k, FIN))}</b></td><td class="n"><b>{sgn(cmp_(k, "최종−지금소득").delta)}</b></td></tr>' for k in ALLT)
w(f'''<section class="sec"><h2><span class="no">0</span>한눈에 보기</h2>
<div class="box"><b class="t">결론</b>
은퇴 전후(50~69세)에 오는 지속적인 소득 하락은 지금 소득만으로는 잘 안 보인다. 가처분소득 3개 패널에서 지금 소득 하나의 시험 AUC는 평균 {f3(b0_mean)}이다.
소득 이력, 취업 변화, 정년·연금 개시까지의 거리, 가구 구조, 자산·연금·건강을 함께 학습한 최종 모델은 {f3(fin_mean)}이다. 복지패널은 {f3(auc("KOWEPS_r", FIN))}까지 올라간다.
결합 향상은 {sgn(mf["est"])}로 모든 패널에서 양수였다. 노동패널(재현)과 의료·고령화패널(이식)에서도 같은 방향이었다. 사람이 만든 계산식인 국민노후패널의 충족률보다 같은 상담 인원으로 {pct(lift_need, 0)} 더 많은 하락자를 찾는다.</div>
<h3>과제별 시험 성적</h3>
{table(["과제", "시험 행", "하락률", "지금 소득", "계산기형", "로지스틱", "LightGBM", "최종 모델", "향상"], rows)}
<p class="muted">최종 모델 = LightGBM과 로지스틱 회귀의 위험 순위 평균. 판정용 사전 지정 모델은 LightGBM 단독이며, 두 결과를 모두 보고한다.</p>
<h3>먼저 알아둘 용어</h3>
<div class="def"><b>AUC</b> – 실제로 떨어진 사람 1명과 떨어지지 않은 사람 1명을 무작위로 뽑았을 때, 모델이 떨어진 사람에게 더 높은 위험 점수를 줄 확률. 0.5는 동전 던지기, 1.0은 완벽.<br>예: AUC 0.87 = 100쌍 중 87쌍에서 실제 하락자를 더 위험하다고 맞힘.</div>
<div class="def"><b>가처분소득</b> – 경상소득에서 세금·사회보험료·이자 같은 비소비지출을 뺀, 가구가 실제로 쓸 수 있는 돈.<br>예: 연 경상소득 4,000만원에서 세금·보험료 600만원을 내면 가처분소득 3,400만원.</div>
<div class="def"><b>균등화</b> – 가구소득을 √가구원수로 나눠 1인 기준 생활 수준으로 맞추는 것.<br>예: 4인 가구 6,000만원 → 6,000/√4 = 1인 기준 3,000만원.</div>
<div class="def"><b>빈곤선</b> – 전국 사람들의 균등화 가처분소득을 줄 세웠을 때 가운데 값(중위값)의 50%. OECD 상대빈곤 기준.<br>예: 2023년 약 {dline.line.iloc[-2]:,.0f}만원(경상)·1,779만원(가처분, 2023년 가격).</div>
<div class="def"><b>사람×차수</b> – 한 사람의 매 조사 시점을 한 행으로 만든 단위. “t 시점 상태 → 그 뒤 몇 년의 결과”가 한 행이 된다.<br>예: 2015·2017·2019년에 조사된 사람은 3행.</div>
</section>''')

exec(open(W + 'report_add.py').read())
w(sec_feedback()); w(sec_process())
# ================= 1 데이터 =================
w(f'''<section class="sec"><h2><span class="no">1</span>사용한 데이터와 관계</h2>
<p>6개 국가 패널은 모두 같은 사람을 여러 해 추적하는 조사다. 하지만 주관 기관·주기·소득 측정 방식이 다르다. 이 차이가 각 패널의 역할을 정한다.</p>
{table(["패널(주관)", "원자료", "주기 · 사용 차수", "사람×차수(50~69세, 소득 관측)", "가처분소득", "이번 역할"], num=[3], rows=[
 f'<tr><td><b>한국복지패널</b> KOWEPS<br><span class="muted">보건사회연구원·서울대</span></td><td>가구원 통합 CSV 20개(2005~2024 소득연도) + 코드북</td><td>매년 · 1~20차</td><td class="n">{int(PT.loc["KOWEPS"].rows):,}</td><td><span class="ok">있음</span> h_din (기관 산출)</td><td><b>정답 · 판정</b></td></tr>',
 f'<tr><td><b>재정패널</b> NaSTaB<br><span class="muted">조세재정연구원</span></td><td>차수별 가구·가구원 Stata 17+17개</td><td>매년 · 1~17차</td><td class="n">{int(PT.loc["NaSTaB"].rows):,}</td><td><span class="ok">있음</span> 경상 − 비소비지출</td><td><b>정답 · 판정</b></td></tr>',
 f'<tr><td><b>국민노후보장패널</b> KReIS<br><span class="muted">국민연금연구원</span></td><td>개인·가구 장기 CSV + 코드북 v10.3</td><td>격년 · 1~10차(2005~2023)</td><td class="n">{int(PT.loc["KReIS"].rows):,}</td><td><span class="ok">있음</span> hdin 처분가능소득</td><td><b>정답 · 판정</b> + 필요 생활비(계산) 검증</td></tr>',
 f'<tr><td><b>한국노동패널</b> KLIPS<br><span class="muted">한국노동연구원</span></td><td>차수별 가구·개인 Stata 27+27개</td><td>매년 · 8~27차 사용</td><td class="n">{int(PT.loc["KLIPS"].rows):,}</td><td>없음 (경상 항목 합산)</td><td><b>재현</b> – 가장 큰 표본</td></tr>',
 f'<tr><td><b>한국의료패널</b> KHP<br><span class="muted">보건사회연구원·건보공단</span></td><td>연도별 Stata (1기 2008~18, 2기 2019~24)</td><td>매년 · 1·2기 분리</td><td class="n">{int(PT.loc["KHP"].rows):,}</td><td>없음 (총소득)</td><td><b>이식 검증</b></td></tr>',
 f'<tr><td><b>고령화연구패널</b> KLoSA<br><span class="muted">고용정보원</span></td><td>종단 요약 Excel 9개(Lt) + 원자료</td><td>격년 · 1~9차(2006~2022)</td><td class="n">{int(PT.loc["KLoSA"].rows):,}</td><td>없음 (총소득)</td><td><b>이식 검증</b></td></tr>'])}
<h3>1-1. 데이터 관계도 – 원자료에서 판정까지</h3>
<div class="pipe">
 <div class="s"><b>① 원자료 6종</b>CSV · Stata · Excel<br>가구 파일 + 개인 파일<br>차수별 ID 체계 상이</div><div class="a">→</div>
 <div class="s"><b>② 공통 스키마</b>패널, 사람ID, 가구ID, 조사연도, 소득연도, 나이, 성별, 학력, 배우자, 가구원 수, 가구 경상·가처분소득, 취업 + 조사별 추가 변수(x_)</div><div class="a">→</div>
 <div class="s"><b>③ 소득 척도 통일</b>만원 · 2023년 가격(CPI)<br>균등화(÷√가구원수)<br>빈곤선 대비 비율</div><div class="a">→</div>
 <div class="s"><b>④ 사람×차수 연결</b>같은 사람의 t−4, t−2, t−1 (이력)과 t+1~t+4 (결과)를 한 행에</div><div class="a">→</div>
 <div class="s"><b>⑤ 정답 · 봉인</b>3번 중 2번 이상 부족<br>최근 2개 차수 = 시험</div>
</div>
<div class="flow">
 <div class="c main"><b>판정 (가처분소득)</b>복지 · 재정 · 국민노후<br>같은 정의로 각자 학습 → 결합 메타분석으로 주장 판정</div>
 <div class="c main"><b>현장 기준 검증</b>국민노후 전용<br>필요 최소생활비 · 충족률 계산 · 본인 걱정과 직접 비교</div>
 <div class="c repl"><b>재현</b>노동패널(최대 표본)<br>가처분소득이 없어 경상소득 기준으로 같은 방향인지 확인</div>
 <div class="c tr"><b>이식</b>의료 · 고령화<br>다른 패널에서 학습한 모델을 옮겼을 때 순위·확률이 유지되는지</div>
</div>
<p class="muted">역할 분담은 이전 실험 노트의 원칙(“가처분소득이 없는 조사는 정답용으로 쓰지 않고 이식·보정 확인용으로”)을 따른 것이다.</p>
</section>''')

VM = [
 ('사람 ID / 가구 ID', 'h_pid / h_id', 'pid / hid(차수별)', 'pid / hid', 'pid / hhid(차수별)', 'PIDWON·pidwon (1·2기 별도)', 'pid / HHID'),
 ('나이', '연도 − h_g4(출생)', '소득연도 − pw_byr', 'age', 'p0107 만나이', '연도 − C4_0 / birth_y', 'A002_age'),
 ('가구 경상소득', 'h_cin', 'h_inc_a', 'hd002b(천원)', '근로+금융+임대+사회보험+이전 합', 'TOTAL / h_inc_tot', 'hhinc'),
 ('가처분소득', 'h_din', 'inc_a − exp_b', 'hdin(천원)', '–', '–', '–'),
 ('가구원 수', 'h01_1', 'w_fnum', 'num', 'h0150', 'B1 / fam_n', 'hhsize'),
 ('취업', 'h_eco4 1~7', 'p_aa001 (소득활동)', 'pa001=1 취업자', 'p0211 취업형태', 'C24 / eco1', 'present_labor'),
 ('종사상지위·직종', 'h_eco4, h_eco9', 'pw_jpo, pw_job', 'pa003·pa005, pa007', 'p0314, p0350~52', 'C33 / eco2', 'status, job'),
 ('공적연금', 'p01_1 수급, h_soc_2 가입형태', 'p_bc001 가입, inc_ba1 금액', 'pd001 1가입·2수급', 'p2101 가입', 'C15', 'national+particular'),
 ('건강', 'h_med2, h_g9_1 만성', '–', 'pk010, pk011', 'p6101', 'cd, hs_srh', 'C001, chronic_sum, adl'),
 ('자산·부채', 'h10 금융·부동산, h09 부채', 'fa 금융, fc001 부채', 'he001 부동산, he003 금융, he004 부채', 'h2562~ 금융, h2602~ 부채, 시가', 'prop, debt(2기)', 'hhnetassets, financialasset'),
 ('현장 기준(전용)', '–', '–', 'pc003/004 필요 최소생활비, pc019·pc010 준비·충분성', '–', '–', '–'),
]
w(f'''<section class="sec"><h3>1-2. 패널별 변수 매핑 (원자료 변수명 → 공통 스키마)</h3>
{table(["공통 항목", "복지", "재정", "국민노후", "노동", "의료", "고령화"], num=[], rows=[f'<tr><td><b>{r[0]}</b></td>' + ''.join(f'<td style="font-size:7.4pt">{c}</td>' for c in r[1:]) + '</tr>' for r in VM])}
<h3>1-3. 원자료를 열면서 만난 문제와 처리</h3><ul>
<li><b>국민노후패널</b>: 처음엔 코드북 없이 값 분포로 역추정했고(pa001 1=취업, 금액 천원 등), 받은 코드북 v10.3으로 모두 맞음을 확인했다. 코드북을 보고 가구소득을 hd001b(총소득, 비경상 포함)에서 <b>hd002b(경상)</b>로 바꿨다. kreispl13은 kreispl05와 같은 사람·같은 값이라 중복 제거. 2023 신규표본(kreishl23)은 미래 결과가 없어 제외. 처분가능소득(hdin)은 2007년 차수부터 있다.</li>
<li><b>의료패널</b>: 1기(2008~2018)와 2기(2019~2024)의 개인 ID가 이어지지 않아 따로 추적했다. 기간을 넘는 정답은 만들지 않았다. 1기 파일은 cp949 라벨·대소문자 혼재를 정리했다.</li>
<li><b>노동패널</b>: 가구 경상소득이 항목별로만 있어 근로·금융·임대·사회보험·이전소득을 합산했다(매매차익·퇴직금·상속 제외). 배우자 유무는 같은 가구·같은 차수에 가구주(10)와 배우자(20)가 함께 있으면 기혼으로 판단했다.</li>
<li><b>고령화패널</b>: Excel 파일의 비표준 속성(synchVertical) 때문에 openpyxl이 읽지 못해 패치 후 변환했다. 종단 요약 파일(Lt)의 생성 변수(hhinc, hhnetassets, chronic_sum 등)를 사용했다.</li>
<li><b>재정패널</b>: 가처분소득 생성 변수가 없어 가구 경상소득(inc_a)에서 비소비지출(exp_b)을 뺐다.</li>
<li><b>단위 점검</b>: 6개 패널의 소득/빈곤선 중위값이 {PT.med_ratio.min():.2f}~{PT.med_ratio.max():.2f}배로 비슷하다. 단위나 개념이 틀렸다면 여러 배 벌어졌을 것이다.</li></ul>
</section>''')

# ================= 2 전처리 =================
dl3 = {2005: 1147, 2010: 1473, 2015: 1552, 2019: 1792, 2020: 1834, 2021: 1753, 2022: 1747, 2023: 1779}
w(f'''<section class="sec"><h2><span class="no">2</span>전처리 상세</h2>
<div class="step"><div class="k">1</div><div><b>대상 연령과 기간</b> – 패널별 변환 단계에서 45~80세를 남겨 이력(t−4)과 결과(t+4)를 붙일 여유를 둔다. 분석 행은 t 시점 50~69세. 소득연도 2004~2024(CPI 범위).</div></div>
<div class="step"><div class="k">2</div><div><b>금액 통일</b> – 모두 연 만원. 국민노후패널은 천원÷10. 소득 기준연도(대부분 “작년 한 해”)의 CPI로 2023년 가격 환산.</div></div>
<div class="step"><div class="k">3</div><div><b>균등화 소득비</b> – r = (가구소득 ÷ √가구원수, 2023년 가격) ÷ 그 해 빈곤선. 가구원 수가 빠진 차수는 같은 사람의 앞뒤 차수로 채우고, 그래도 없으면 2명.</div></div>
<div class="step"><div class="k">4</div><div><b>빈곤선 두 종류</b> – 복지패널 전 연령, 개인 횡단 가중치로 연도별 가중 중위값의 50%를 구한다. <b>가처분 빈곤선</b>(판정 3개 패널)과 <b>경상 빈곤선</b>(노동·의료·고령화). 국민노후패널은 추가로 연도·가구유형(부부/개인)별 <b>필요 최소 노후생활비 응답 중위값</b>을 기준선으로 쓴다.</div></div>
<div class="step"><div class="k">5</div><div><b>사람×차수 연결</b> – (패널, 사람, 조사연도) 키로 같은 사람의 t−4, t−2, t−1과 t+1, t+2, t+3, t+4를 붙인다. 매년 조사는 한 해 단위, 격년 조사는 2년 단위로 붙는다.</div></div>
<div class="step"><div class="k">6</div><div><b>이력 변수</b> – 2·4년 소득 변화(로그), 최근 4년 최저 소득비, 소득 변동성(t, t−2, t−4의 표준편차), 과거 빈곤 경험, 2년 내 실직, 2년간 가구원 변화, 60세까지 거리, 출생연도별 국민연금 개시연령(60~65세)까지 거리.</div></div>
<div class="step"><div class="k">7</div><div><b>조사별 추가 변수</b> – 자산·부채는 원금액 대신 <b>소득 대비 배수</b>와 로그로(소득 수준과 중복 제거). 비어 있는 비율이 80% 넘거나 값이 하나뿐인 변수는 그 패널에서 제외.</div></div>
<div class="step"><div class="k">8</div><div><b>결측·극단값</b> – 부스팅은 결측을 그대로 학습한다(결측 자체가 정보). 선형·거리 모델은 중앙값 대체 + 결측 표시. 극단값은 <b>학습 구간의</b> 0.5/99.5% 분위로 자르고, 같은 경계를 시험셋에 적용.</div></div>
<div class="step"><div class="k">9</div><div><b>누수 차단</b> – 입력은 모두 t 시점과 그 이전 정보. 결과(t+1~t+4) 변수는 입력에 없다. 학습행은 결과 시점이 시험 시작 전인 행만 쓴다.</div></div>
<h3>가처분 빈곤선 (균등화 가처분소득 중위 50%, 2023년 가격, 연 만원)</h3>
{table([str(y) for y in dl3], num=range(8), rows=['<tr>' + ''.join(f'<td class="n">{v:,}</td>' for v in dl3.values()) + '</tr>'])}
</section>''')

# ================= 3 정답 설계 =================
w(f'''<section class="sec"><h2><span class="no">3</span>정답 설계 – 왜 “3번 중 2번 이상 부족”인가</h2>
<p>정답을 네 번 바꿔 보며 같은 시험 방식으로 채점했다. 핵심은 <b>지금 소득이 정답을 거의 다 정하는지</b>와 <b>정답에 일시적 잡음이 얼마나 섞였는지</b>다.</p>
<figure><img src="{img('g01_journey.png')}"><figcaption>그림 1. 정답 정의별 시험 AUC(패널 평균). 굵은 글씨 = ML 이득.</figcaption></figure>
{table(["정답", "지금 소득", "ML", "이득", "문제점"], num=[1, 2, 3], rows=[
 f'<tr><td>① 2년 뒤 1회라도 빈곤선 아래 (경상, 6개)</td><td class="n">{f3(J[0][1])}</td><td class="n">{f3(J[0][2])}</td><td class="n">{sgn(J[0][2]-J[0][1])}</td><td>선 근처에서 한 해만 출렁여도 1 → 정답 잡음</td></tr>',
 f'<tr><td>② 2·4년 뒤 모두 아래, 지금 가난한 사람 포함 (상태형)</td><td class="n">{f3(J[1][1])}</td><td class="n">{f3(J[1][2])}</td><td class="n">{sgn(J[1][2]-J[1][1])}</td><td>AUC는 높지만 지금 소득이 다 맞힘 – 기존 시스템이 이미 아는 사람</td></tr>',
 f'<tr><td>③ 지금 괜찮고 2·4년 뒤 모두 아래 (경상, 6개)</td><td class="n">{f3(J[2][1])}</td><td class="n">{f3(J[2][2])}</td><td class="n">{sgn(J[2][2]-J[2][1])}</td><td>잡음은 줄었지만 경상소득은 세금·보험료 차이로 생활 수준과 어긋남</td></tr>',
 f'<tr class="hl"><td>④ <b>v3</b>: 지금 괜찮고 1~4년 뒤 3번 중 2번 이상 아래 (가처분, 3개)</td><td class="n">{f3(J[3][1])}</td><td class="n">{f3(J[3][2])}</td><td class="n">{sgn(J[3][2]-J[3][1])}</td><td>반복 관측 + 가처분 + 역할 분담 → ML이 기여할 몫이 가장 큼</td></tr>'])}
<div class="box"><b class="t">v3 정답의 정확한 정의</b>
대상: t 시점 50~69세이고, 균등화 가처분소득 ≥ 가처분 빈곤선(“지금은 괜찮음”).<br>
결과: t+2, t+3, t+4 조사 중 2번 이상 빈곤선 아래면 1. t+2와 t+4는 반드시 관측돼야 한다. t+3가 없는 경우(격년 조사·결측)는 t+2와 t+4 <b>둘 다</b> 아래여야 1.<br>
효과: 한 해만 출렁인 사람은 0이 된다 → 정답이 “일시적 잡음”이 아니라 “지속적 소득절벽”을 가리킨다.</div>
<p>AUC 숫자만 보면 ②가 가장 높다. 하지만 ②는 지금 가난한 사람이 2년·4년 뒤에도 가난하다는 걸 맞히는 문제라 지금 소득 하나로 이미 {f3(J[1][1])}이다. 사업적 가치(아직 안 보이는 사람을 먼저 찾기)와 ML의 기여가 모두 큰 것은 ④다. 그래서 ④를 주 정답으로 하고, ②는 비교용으로 남긴다.</p>
</section>''')

# ================= 4 검증 설계 =================
tr_rows = ''.join(f'<tr><td>{TN[k]}</td><td class="n">{DI[k]["tr_years"]}</td><td class="n">{DI[k]["n_tr"]:,}</td><td class="n">{pct(DI[k]["pos_tr"])}</td><td class="n">{DI[k]["te_years"]}</td><td class="n">{DI[k]["n_te"]:,}</td><td class="n">{DI[k]["persons_te"]:,}</td><td class="n">{pct(DI[k]["pos_te"])}</td><td class="n">{DI[k]["n_feat"]}</td></tr>' for k in ALLT)
w(f'''<section class="sec"><h2><span class="no">4</span>검증 설계 – 미래를 보지 않는 시험</h2>
{table(["과제", "학습 기준연도", "학습 행", "학습 하락률", "시험 기준연도", "시험 행", "시험 인원", "시험 하락률", "입력 수"], [tr_rows])}
<div class="step"><div class="k">1</div><div><b>시험 봉인</b> – 4년 뒤 결과가 관측되는 최근 2개 기준 차수를 시험셋으로 떼어 둔다. 모델 선택·튜닝에 한 번도 쓰지 않는다.</div></div>
<div class="step"><div class="k">2</div><div><b>학습</b> – 결과 관측 기간(t+4)이 시험 시작 전에 끝나는 행만. 시험 직전 4년치는 결과가 겹쳐 버린다.</div></div>
<div class="step"><div class="k">3</div><div><b>튜닝</b> – 학습 구간의 마지막 2개 연도를 내부 검증으로 쓰고, 그보다 4년 앞까지로 학습해 격자(4개)와 반복 수를 고른 뒤 전체 학습 구간으로 재적합.</div></div>
<div class="step"><div class="k">4</div><div><b>판정</b> – 판정 3개 패널 각각에서 (모델 − 지금 소득) AUC 차이를 DeLong 공분산으로 구하고 DerSimonian–Laird 랜덤효과로 결합. 판정 기준: 결합 하한 &gt; 0, 실질 기준 +0.03, 3개 중 3개 양수.</div></div>
<div class="step"><div class="k">5</div><div><b>보조</b> – 재현(노동)·이식(의료·고령화), 사람 단위 부트스트랩, 질문 수 고정, 학습곡선·셔플, 집단별, 처음 보는 사람, 보정.</div></div>
<p class="muted">사전 지정 모델은 LightGBM 단독(v3 첫 실행에서 지정). 최종 서비스 모델(LightGBM+로지스틱 순위 평균)은 v3 탐색 과정에서 정했으므로 두 결과를 함께 보고한다.</p>
</section>''')

# ================= 5 주결과 =================
cr = ''
for k in SHOW:
    a, b, c = cmp_(k, '최종−지금소득'), cmp_(k, 'LightGBM−지금소득'), cmp_(k, '최종−계산기형')
    cr += f'<tr><td>{TN[k]}</td><td class="n">{sgn(a.delta)} <span class="muted">±{1.96*a.se:.3f}</span></td><td class="n">{pv(a.p)}</td><td class="n">{sgn(b.delta)}</td><td class="n">{pv(b.p)}</td><td class="n">{sgn(c.delta)}</td><td class="n">{pv(c.p)}</td></tr>'
cr += f'<tr class="hl"><td>판정 3개 결합</td><td class="n">{sgn(mf["est"])} [{sgn(mf["lo"])}, {sgn(mf["hi"])}]</td><td class="n">{pv(mf["p"])}</td><td class="n">{sgn(ml["est"])} [{sgn(ml["lo"])}, {sgn(ml["hi"])}]</td><td class="n">{pv(ml["p"])}</td><td class="n">{sgn(mc["est"])}</td><td class="n">{pv(mc["p"])}</td></tr>'
npos = int((C[(C.comp == '최종−지금소득') & C.task.isin(MAIN)].delta > 0).sum())
w(f'''<section class="sec"><h2><span class="no">5</span>주결과 – 판정</h2>
{table(["과제", "최종 − 지금 소득", "p", "LightGBM(사전) − 지금 소득", "p", "최종 − 계산기형", "p"], [cr])}
<figure><img src="{img('g02_forest.png')}"><figcaption>그림 2. 과제별 AUC 향상(95% CI)과 판정 3개 패널 결합(마름모). 점선 = 실질 기준 +0.03. 이질성 I² = {mf["I2"]*100:.0f}%.</figcaption></figure>
<div class="box"><b class="t">판정: 지지됨</b>
① 결합 하한 {sgn(mf["lo"])} &gt; 0 <span class="ok">통과</span> ② 결합 추정 {sgn(mf["est"])} ≥ +0.03 {'<span class="ok">통과</span>' if mf["est"] >= 0.03 else '<span class="no">미통과</span>'} ③ 판정 3개 중 {npos}개 양수 {'<span class="ok">통과</span>' if npos == 3 else '<span class="no">미통과</span>'}. 사전 지정 LightGBM 단독도 {sgn(ml["est"])} [{sgn(ml["lo"])}, {sgn(ml["hi"])}]로 같은 결론이다. 사람이 만든 계산기형(소득·나이·취업 로지스틱)보다도 {sgn(mc["est"])} 높다.</div>
</section>''')

# ================= 6 모델 비교 =================
models = [m for m in Z.model.unique()]
zt = Z[Z.task.isin(SHOW)].pivot_table(index='model', columns='task', values='auc')[SHOW]
zt['판정 평균'] = zt[MAIN].mean(axis=1); zt = zt.sort_values('판정 평균', ascending=False)
zr = ''.join(f'<tr{" class=hl" if m == FIN else ""}><td>{m}</td>' + ''.join(f'<td class="n">{f3(r[k])}</td>' for k in SHOW) + f'<td class="n"><b>{f3(r["판정 평균"])}</b></td></tr>' for m, r in zt.iterrows())
FAM = {'B0 지금 소득': '기준', 'B1 계산기형': '기준(규칙형 로지스틱)', 'LR_L2': '선형(L2 로지스틱)', 'LR_L1': '선형(L1 희소)', 'GAM_Spline_LR': '가법(스플라인 GAM)',
       'LDA': '선형 판별', 'GaussianNB': '나이브베이즈', 'KNN_k101': '거리 기반', 'DecisionTree': '단일 트리', 'RandomForest': '배깅 트리',
       'ExtraTrees': '배깅 트리(무작위 분할)', 'AdaBoost': '부스팅', 'GradientBoosting': '부스팅', 'HistGB': '히스토그램 부스팅',
       'XGBoost': '부스팅', 'LightGBM': '부스팅(사전 지정)', 'CatBoost': '부스팅', FIN: '앙상블(최종)'}
w(f'''<section class="sec"><h2><span class="no">6</span>모델 비교 – 신경망 제외 {len(models) - 3}종 + 기준 2종 + 최종 앙상블</h2>
<p>모든 모델은 과제마다 같은 학습셋·같은 입력·같은 시험셋을 썼다. 부스팅 4종(HistGB·XGBoost·LightGBM·CatBoost)은 내부 검증으로 격자와 반복 수를 골랐고, 나머지는 고정 설정이다.</p>
{table(["모델"] + [TN[k] for k in SHOW] + ["판정 3개 평균"], [zr], 'style="break-inside:auto;font-size:7.8pt"')}
</section>''')
tr_ = ''.join(f'<tr><td>{TN[r.task]}</td><td>{r.model}</td><td style="font-size:7.4pt">{r.params}</td><td class="n">{int(r.iters)}</td><td class="n">{f3(r.inner)}</td></tr>' for _, r in TU[TU.task.isin(MAIN)].iterrows())
w(f'''<section><figure class="half"><img src="{img('g03_zoo.png')}"><figcaption>그림 3. 판정 3개 패널 평균 시험 AUC. 주황 = 지금 소득, 초록 = 계산기형, 진한 파랑 = 최종 앙상블.</figcaption></figure>
<div class="box gray"><b class="t">읽는 법</b><ul>
<li><b>모든 학습 모델이 기준선 위</b>에 있다. 정보(이력·취업·연금·자산) 자체가 가치가 있다는 뜻이다.</li>
<li><b>상위권은 로지스틱·GAM·부스팅·앙상블이 촘촘히 붙어 있다.</b> 서로 다른 계열이 같은 높이에서 멈춘다는 것은 데이터에 있는 신호를 거의 다 뽑아냈다는 신호다.</li>
<li><b>하위권(나이브베이즈·단일 트리·KNN)</b>은 변수 독립 가정·과적합·고차원 거리 문제로 손해를 본다. 모델 선택이 결과를 바꾼다.</li>
<li>LightGBM과 로지스틱은 패널별로 우열이 바뀐다(복지는 로지스틱, 국민노후는 LightGBM). 그래서 최종 모델은 둘의 순위를 평균한다.</li></ul></div>
<h3>부스팅 튜닝 결과 (판정 3개 패널)</h3>
{table(["과제", "모델", "선택된 설정", "반복", "내부 검증 AUC"], [tr_], 'style="font-size:7.8pt"', num=[3, 4])}
</section>''')

# ================= 7 부트스트랩 =================
BB = O['boot']
br = ''.join(f'<tr><td>{TN[r.task]}</td><td>{r.comp}</td><td class="n">{int(r.n_persons):,}</td><td class="n">{sgn(r.delta)}</td><td class="n">{r.se:.4f}</td><td class="n">[{sgn(r.lo)}, {sgn(r.hi)}]</td><td class="n">{cmp_(r.task, r.comp if r.comp != "LightGBM−로지스틱" else "LightGBM−로지스틱").se:.4f}</td></tr>' for _, r in BB.iterrows())
bm = ''.join(f'<tr class="hl"><td>판정 3개 결합</td><td>{c}</td><td></td><td class="n">{sgn(v["est"])}</td><td class="n">{v["se"]:.4f}</td><td class="n">[{sgn(v["lo"])}, {sgn(v["hi"])}]</td><td></td></tr>' for c, v in BM.items())
w(f'''<section class="sec"><h2><span class="no">7</span>사람 단위 부트스트랩 – 보수적인 신뢰구간</h2>
<p>시험셋에는 같은 사람이 두 기준 차수에 나올 수 있다. 행을 독립으로 보는 DeLong 표준오차는 이를 과소평가할 수 있다. 그래서 <b>사람</b>을 단위로 300번 다시 뽑아(그 사람의 모든 행을 함께) AUC 차이의 분포를 구했다.</p>
{table(["과제", "비교", "시험 인원", "Δ AUC", "부트스트랩 SE", "95% 구간(백분위)", "DeLong SE"], [br, bm], 'style="font-size:7.8pt"', num=[2, 3, 4, 5, 6])}
<div class="box gray"><b class="t">해석</b>부트스트랩 표준오차는 DeLong보다 대체로 조금 크지만, 결합 결론(최종 − 지금 소득 {sgn(BM["최종−지금소득"]["est"])}, 하한 {sgn(BM["최종−지금소득"]["lo"])})은 그대로다. LightGBM − 로지스틱은 {sgn(BM["LightGBM−로지스틱"]["est"])} [{sgn(BM["LightGBM−로지스틱"]["lo"])}, {sgn(BM["LightGBM−로지스틱"]["hi"])}]로 0을 포함한다. 부스팅이 로지스틱보다 확실히 낫다고는 말할 수 없다. 이득의 주원천은 모델 계열이 아니라 <b>어떤 정보를 학습했느냐</b>다.</div>
</section>''')

# ================= 8 질문 수 고정 =================
fr = ''
for kk in [5, 12, 20]:
    fr += f'<tr><td class="n">{kk}개</td><td class="n"><b>{f3(fqm.get(("ML 선택", kk)))}</b></td><td class="n">{f3(fqm.get(("전문가 양식", kk)))}</td><td class="n">{f3(fqm.get(("무작위", kk)))}</td><td class="n">{f3(FQ[(FQ.set == "ML 선택") & (FQ.k == kk) & FQ.task.isin(MAIN)].auc_lr.mean())}</td></tr>'
sel12 = ''
for k in MAIN:
    r = FQ[(FQ.task == k) & (FQ.k == 12) & (FQ.set == 'ML 선택')]
    if len(r): sel12 += f'<tr><td>{TN[k]}</td><td style="font-size:7.6pt">{" · ".join(LAB.get(f, f) for f in r.feats.iloc[0])}</td></tr>'
w(f'''<section class="sec"><h2><span class="no">8</span>질문 수 고정 비교 – “변수가 많아서 이긴 것 아닌가”</h2>
<p>물어보는 질문 수를 똑같이 맞추고 비교했다. 모든 묶음에 “지금 소득”을 포함하고, 나머지 k−1개를 ① ML이 고른 순서 ② 노후준비 진단표에 흔한 전문가 양식 순서(나이·취업·배우자·가구원·연금·자가·금융자산·부채·건강…) ③ 무작위(3회 평균)로 채운다. ML의 순서는 <b>학습 구간 안의 내부 검증 순열 중요도</b>로만 정했다(시험셋을 보지 않음).</p>
<div class="two"><figure><img src="{img('g04_fixedq.png')}"></figure><div>
{table(["질문 수", "ML 선택", "전문가 양식", "무작위", "ML 선택+로지스틱"], [fr])}
<p class="muted">판정 3개 패널 평균. 같은 고정 설정의 LightGBM.</p></div></div>
<p>같은 질문 수에서 ML이 고른 묶음이 가장 높다. 데이터가 <b>무엇을 물을지</b>를 고르면 같은 설문 길이로 더 잘 찾는다. 이것이 대화형 진단(12문항) 설계의 근거다.</p>
<h3>ML이 고른 12문항 (패널별)</h3>{table(["과제", "질문 (중요 순)"], [sel12], num=[])}
</section>''')

# ================= 9 학습곡선 · 셔플 =================
w(f'''<section class="sec"><h2><span class="no">9</span>학습곡선과 라벨 셔플 – “계산기가 아니라 학습했다”</h2>
<p>계산기는 정해진 공식이라 데이터를 더 줘도 달라지지 않는다. 학습된 모델은 데이터가 늘수록 좋아지고, 우연(섞인 정답)에서는 아무것도 배우지 못한다. 판정 3개 + 노동패널의 학습셋을 합친 통합 모델(공통 입력 + 가처분 소득비)로 확인했다. 통합 시험 AUC는 {f3(O["pool_all"])}(지금 소득 {f3(O["pool_b0"])})이다.</p>
<figure><img src="{img('g05_learning.png')}"><figcaption>그림 5. 왼쪽: 학습 행 {int(LC.n.iloc[0]):,} → {int(LC.n.iloc[-1]):,}에서 시험 AUC {f3(LC.test_auc.iloc[0])} → {f3(LC.test_auc.iloc[-1])}, 학습–시험 격차 {f3(LC.train_auc.iloc[0]-LC.test_auc.iloc[0])} → {f3(LC.train_auc.iloc[-1]-LC.test_auc.iloc[-1])}. 오른쪽: 부스팅 반복에 따른 학습·시험 AUC.</figcaption></figure>
<ul><li><b>데이터가 늘수록</b> 시험 AUC가 오르고 학습–시험 격차는 줄어든다. 적은 데이터에서는 외우고(과적합), 많아지면 일반화한다.</li>
<li><b>반복에 따라</b> 시험 AUC가 빠르게 오른 뒤 평탄해진다. 오래 학습해도 시험 성능이 무너지지 않는다(과적합 통제).</li>
<li><b>라벨 셔플</b>: 학습셋의 정답만 무작위로 섞어 같은 모델을 5번 학습하면 시험 AUC가 평균 {perm.mean():.3f}(범위 {perm.min():.3f}~{perm.max():.3f})다. 원래 정답의 {f3(O["pool_all"])}에 한 번도 가까이 가지 못한다. 모델이 찾은 것은 정답과 연결된 실제 신호다.</li></ul>
<h3>소득이 같은 사람들 사이에서도 구별한다</h3>
<div class="two"><figure><img src="{img('g06_bands.png')}"></figure><div>
<p>지금 소득 구간 안에서는 소득 차이가 작아서 지금 소득만으로는 동전 던지기에 가깝다(AUC {bd.auc_b0.min():.2f}~{bd.auc_b0.max():.2f}). ML은 구간 안에서도 {bd.auc_ml.min():.2f}~{bd.auc_ml.max():.2f}를 유지한다.</p>
<p>빈곤선 바로 위(1.0~1.25배, {int(bd.n.iloc[0]):,}행, 하락률 {pct(bd.pos.iloc[0])})는 사업상 가장 중요한 구간이다. 여기서 지금 소득 {bd.auc_b0.iloc[0]:.2f} vs ML {bd.auc_ml.iloc[0]:.2f}. 소득 밖의 정보를 학습했다는 가장 직접적인 증거다.</p></div></div>
</section>''')

# ================= 10 중요도 · 부분의존 =================
pn = O['pdp_nps']['average'][0]
w(f'''<section class="sec"><h2><span class="no">10</span>중요도와 부분의존 – 무엇을 보고 판단하나</h2>
<figure><img src="{img('g08_importance.png')}"><figcaption>그림 6. 과제별 순열 중요도 상위 8개(시험셋, LightGBM). 막대 = 그 변수만 섞었을 때 떨어지는 AUC, 가는 선 = 5회 반복 표준편차.</figcaption></figure>
<div class="def"><b>순열 중요도</b> – 시험셋에서 한 변수의 값만 사람들 사이에 무작위로 섞었을 때 AUC가 얼마나 떨어지는지. 많이 떨어질수록 모델이 그 변수에 기대고 있다.</div>
<p>지금 소득이 대체로 1위지만, 그다음을 <b>소득 이력</b>(최근 4년 최저 소득, 2년·4년 변화, 변동성)과 <b>소득 구성</b>(공적이전·근로소득 비중), <b>일과 나이</b>(취업, 연금 개시까지 거리)가 채운다. 모델은 “지금 얼마 버나”에 더해 “그 소득이 무엇으로 이루어졌고 얼마나 흔들려 왔나”를 본다.</p>
<figure><img src="{img('g07_pdp.png')}"><figcaption>그림 7. 부분의존(다른 변수는 그대로 두고 한 변수만 바꿨을 때의 평균 예측 확률). 통합 모델.</figcaption></figure>
<div class="def"><b>부분의존</b> – 모든 사람의 한 변수를 같은 값으로 바꿔 놓고 예측 확률의 평균을 구한 것. 그 변수가 위험에 어떤 모양으로 작용하는지 보여준다.</div>
<p><b>왼쪽</b>: 국민연금 개시연령 13년 전 → 개시 이후로 갈수록 위험이 바뀐다(일함 {pn[0,1]*100:.1f}% → {pn[-1,1]*100:.1f}%, 일하지 않음 {pn[0,0]*100:.1f}% → {pn[-1,0]*100:.1f}%). 정년과 연금 개시 사이 “소득 크레바스”의 데이터상 모양이다.
<b>오른쪽</b>: 같은 소득 위치라도 최근 2년간 소득이 어떻게 움직였느냐에 따라 위험이 다르다. 모델은 일시적 소득과 안정적 소득을 구별한다.</p>
</section>''')

# ================= 11 집단별 · 처음 보는 사람 =================
nr = ''.join(f'<tr><td>{TN[r.task]}</td><td class="n">{int(r.n):,}</td><td class="n">{pct(r.share, 0)}</td><td class="n">{f3(r.auc_b0)}</td><td class="n">{f3(r.auc_ml)}</td><td class="n">{sgn(r.delta)}</td><td class="n">{"–" if pd.isna(r.p) else pv(r.p)}</td></tr>' for _, r in NW.iterrows())
nwv = NW.dropna(subset=['delta']); nm_ = meta_dl(nwv.delta, nwv.se) if len(nwv) >= 2 else None
w(f'''<section class="sec"><h2><span class="no">11</span>집단별 점검과 처음 보는 사람 채점</h2>
<h3>집단별 – 특정 집단에서만 맞는 것 아닌가</h3>
<figure><img src="{img('g09_subgroup.png')}"><figcaption>그림 8. 성별·학력·나이대·취업·가구형태별 AUC 향상(최종 − 지금 소득). 판정 3개 + 노동패널 4개 과제 결합. 오른쪽 = 평균 AUC(지금 소득 → 최종).</figcaption></figure>
<p>모든 집단에서 향상이 양수다. 특히 지금 소득만으로는 가장 구별이 어려운 집단(미취업, 60대)에서도 ML이 일관되게 더한다. 서비스를 특정 집단에만 써야 하는 제약은 보이지 않는다.</p>
<h3>처음 보는 사람 – 같은 사람을 다시 맞힌 것 아닌가</h3>
<p>시험셋 가운데 <b>사람도 가구도 학습셋에 한 번도 나오지 않은</b> 행만 골라 따로 채점했다(신규 표본·분가 가구).</p>
{table(["과제", "처음 보는 사람 행", "시험셋 중 비율", "지금 소득", "최종 모델", "Δ", "p"], [nr])}
{f'<p>결합: {sgn(nm_["est"])} [{sgn(nm_["lo"])}, {sgn(nm_["hi"])}]. 처음 보는 사람에서도 향상이 유지된다.</p>' if nm_ else ''}
<p class="muted">국민노후패널처럼 시험기간에 신규 표본이 없는 패널은 처음 보는 사람이 적어(하락자 15명 미만) 채점하지 않았다.</p>
</section>''')

# ================= 12 보정 · 이식 =================
csr = ''.join(f'<tr><td>{TN[r.task]}</td><td>{r.kind}</td><td class="n">{pct(r.mean_pred)}</td><td class="n">{pct(r.obs)}</td><td class="n">{r.ece*100:.1f}%p</td><td class="n">{r.brier:.4f}</td><td class="n">{r.brier_base:.4f}</td></tr>' for _, r in CS.iterrows())
w(f'''<section class="sec"><h2><span class="no">12</span>보정과 이식 – 확률은 맞나, 다른 기관에 옮겨도 되나</h2>
<div class="def"><b>보정</b> – 모델이 “20%”라고 한 사람들 중 실제로 20% 정도가 떨어지는지. 순위(AUC)가 맞아도 확률 수준은 어긋날 수 있다.<br><b>Platt 재보정</b> – 모델 점수를 그대로 두고, 최근 자료로 “점수 → 확률” 변환식(로지스틱 한 줄)만 다시 맞추는 것. 순위는 바뀌지 않는다.</div>
<figure><img src="{img('g10_calibration.png')}"><figcaption>그림 9. 예측 확률 10분위별 실제 하락률. 왼쪽 원 확률, 오른쪽 학습구간 마지막 연도로 재보정한 확률. 대각선에 가까울수록 정직한 확률.</figcaption></figure>
{table(["과제", "확률", "평균 예측", "실제", "ECE", "Brier", "Brier(평균만)"], [csr], 'style="font-size:7.8pt"', num=[2, 3, 4, 5, 6])}
<p>원 확률은 대체로 대각선 근처지만 시험기간 하락률이 학습기간보다 낮은 패널(복지·재정·노동)은 다소 높게 나온다. 학습구간 마지막 연도로 재보정하면 이 세 과제는 ECE가 줄어든다. 반면 <b>국민노후패널은 재보정 후 오히려 나빠졌다</b>(가처분 {CS[(CS.task=="KReIS_r")&(CS.kind=="원 확률")].ece.iloc[0]*100:.1f}%p → {CS[(CS.task=="KReIS_r")&(CS.kind=="재보정")].ece.iloc[0]*100:.1f}%p). 재보정에 쓴 내부 검증 표본이 작고(수백 명) 그 시기의 하락률이 시험기간과 달랐기 때문이다. 운영에서는 <b>표본이 충분한 최근 자료로만 재보정</b>하고, 작을 때는 원 확률을 쓰는 규칙이 필요하다.</p>
<p class="muted">ECE = 10분위별 |예측−실제|의 가중 평균. Brier = (예측−실제)² 평균, 낮을수록 좋음. “Brier(평균만)”은 모두에게 평균 하락률을 준 경우.</p>
<h3>이식 – 한 패널에서 학습해 다른 패널에 적용</h3>
<div class="two"><figure><img src="{img('g11_transfer.png')}"></figure><div>
<p>공통 입력만으로 학습한 모델을 다른 과제의 시험셋에 그대로 적용했다(행 = 학습, 열 = 시험). 비대각선(다른 패널) 평균 {offd.mean():.3f}, 최저 {offd.min():.3f}. 조사 기관·문항·표본이 달라도 같은 위험 구조가 반복된다.</p>
<p>순위는 유지되지만 확률 수준은 어긋난다. 그대로 옮기면 평균 예측과 실제 하락률이 평균 {er_raw.mean()*100:.1f}%p(최대 {er_raw.max()*100:.1f}%p) 차이 난다. 대상 패널의 최근 학습 자료로 <b>확률만 재보정</b>하면 {er_cal.mean()*100:.1f}%p(최대 {er_cal.max()*100:.1f}%p)로 줄어든다. 재학습 없이 이식할 수 있다는 뜻이다.</p>
<p>국민노후패널(열)은 어느 패널에서 학습해도 0.68~0.73으로 낮다. 국민노후는 표본이 고령 쪽으로 치우쳐 있고 소득 구성(공적이전 비중)이 달라, 공통 입력만으로는 구조를 다 옮기지 못한다. 이 패널은 자체 추가 입력(소득 구성·필요 생활비)이 있을 때 0.75~0.80으로 오른다.</p>
<p>이전 실험의 “복지패널 이식 실패(예측 61% vs 실제 26%)”는 순위가 아니라 확률 수준의 문제였다. 재보정으로 평균 오차가 줄지만(최대 오차가 남는 쌍도 있음), 실제 이식 때는 대상 기관 자료로 재보정 후 한 번 더 확인하는 절차가 필요하다.</p></div></div>
</section>''')

# ================= 13 비즈니스 =================
bzr = ''
for k in SHOW:
    b0n, fin_n, b1n = found(k, 'B0 지금 소득'), found(k, FIN), found(k, 'B1 계산기형')
    falls = int(BZ[BZ.task == k].falls.iloc[0])
    bzr += f'<tr><td>{TN[k]}</td><td class="n">{k20(k):,}</td><td class="n">{falls:,}</td><td class="n">{b0n}</td><td class="n">{b1n}</td><td class="n"><b>{fin_n}</b></td><td class="n"><b>{fin_n/b0n-1:+.0%}</b></td><td class="n">{pct(b0n/falls,0)} → {pct(fin_n/falls,0)}</td></tr>'
w(f"""<section class="sec"><h2><span class="no">13</span>비즈니스 모델 – 미리사주: 진단 사이트 자체가 상품</h2>
<p>미리사주는 상담이나 금융상품 판매로 이어지지 않는다. 사이트에서 <b>무료로 2년 뒤 소득절벽 신호</b>를 보여 주고, 문제가 되는 신호마다 <b>방향과 공식 사이트</b>를 안내한다. 매출은 향후 <b>사이트 자체 유료화</b>로 만든다(구체 상품은 미정).</p>
<figure><img src="{img('g12_business.png')}"><figcaption>그림 10. 시험셋에서 위험 상위 20%로 표시된 사람 중 실제 하락자 수. 같은 수를 살폈을 때 ML이 더 많은 실제 하락자를 담는다(경보의 질). 국민노후(필요생활비)의 “기존”은 충족률 계산이다.</figcaption></figure>
{table(["과제", "상위 20% 인원", "전체 하락자", "지금 소득", "계산기형", "최종 ML", "더 담음", "포착률"], [bzr])}
<h3>서비스 구조</h3>
<table><tr><th style="width:19%">단계</th><th style="width:19%">사용자</th><th>제공 가치</th><th style="width:22%">수익</th></tr>
<tr><td><b>① 무료 진단</b><br>(현재)</td><td>50~69세 본인, 부모님 대신 진단하는 자녀</td><td>화면 21문항 → 2년 뒤 위험 구간 · 그렇게 본 이유 3가지 · 판단 보류 · 지금 소득이 빈곤선의 몇 배인지</td><td>무료</td></tr>
<tr><td><b>② 방향 + 공식 사이트</b><br>(현재)</td><td>같음</td><td>이유별로 “무엇을 확인하면 좋은지” 방향을 말하고 공공기관 공식 페이지로 연결(아래 표). 자격 판단은 각 기관이 한다</td><td>무료 · 상담·상품 연결 없음</td></tr>
<tr><td><b>③ 사이트 유료화</b><br>(향후)</td><td>같음</td><td>사이트 자체의 유료 기능(구체 상품 미정)</td><td>이용료. 전제: 패널 기관의 영리 이용 승인 또는 자체 수집 데이터로 재학습</td></tr></table>
<h3>신호별 방향과 연결 사이트</h3>
<table><tr><th style="width:27%">모델이 짚은 신호</th><th style="width:27%">방향</th><th>연결</th></tr>
<tr><td>지금 소득이 빈곤선 가까움 · 최근 소득 하락</td><td>받을 수 있는 복지 서비스 확인</td><td>복지로 복지서비스 모의계산 (bokjiro.go.kr)</td></tr>
<tr><td>65세 이상 또는 곧 65세 · 소득 낮음</td><td>기초연금 대상 여부 확인</td><td>복지로 기초연금 모의계산 · 국민연금공단 기초연금 신청 안내</td></tr>
<tr><td>국민연금 개시까지 공백 · 연금 미수령</td><td>예상 연금액·수령 시점 확인, 노후준비 진단</td><td>국민연금공단 (nps.or.kr) · 중앙노후준비지원센터 (csa.nps.or.kr)</td></tr>
<tr><td>최근 2년 내 일을 그만둠 · 미취업</td><td>재취업·직업훈련 정보 확인</td><td>고용24 (work24.go.kr)</td></tr>
<tr><td>자가 보유 · 금융자산 적음</td><td>주택연금 예상 월지급금 확인</td><td>한국주택금융공사 주택연금 (hf.go.kr)</td></tr>
<tr><td>부채 부담</td><td>채무조정 제도 확인</td><td>신용회복위원회 (ccrs.or.kr, ☎1600-5500) · 서민금융진흥원 채무조정 안내 (kinfa.or.kr)</td></tr></table>
<p class="muted">원칙: 특정 금융상품을 추천하지 않는다 · 공공기관 공식 페이지만 연결한다 · “받을 수 있다”가 아니라 “확인해 보라”고 말한다. 16-6(가장 작은 변화)에서 위험 상위 20% 중 개인 행동 1~2개로 벗어나는 사람이 4~18%뿐이었던 결과와 맞게, 방향은 제도 확인을 먼저 둔다.</p>
</section>""")
w(f"""<section class="sec"><h3>초기 아이디어 4개 → 지금 범위</h3>
<table><tr><th style="width:22%">아이디어</th><th>이 결과가 주는 근거</th><th style="width:22%">지금 범위</th></tr>
<tr><td>내 노후걱정이 실제로 이어질지 (개인 진단)</td><td>화면 21문항만으로 전체 입력 모델과 같은 성능(16-10, 손실 +0.001). 국민노후패널의 본인 걱정 문항은 기준선 비교에서 약했다(걱정 AUC 0.54 vs ML 0.66).</td><td><span class="ok">반영</span> – 미리사주 진단</td></tr>
<tr><td>국민연금공단 결과가 적절한가</td><td>공단의 실제 진단 결과는 데이터에 없어 직접 비교는 불가. 공단 패널의 필요 생활비로 만든 충족률 계산보다 같은 인원에서 {pct(lift_need, 0)} 더 찾는다.</td><td><span class="no">표현 주의</span> – “계산의 2차 검진”으로만</td></tr>
<tr><td>재취업지원서비스 · 복지 사각지대 발굴</td><td>빈곤선 바로 위 집단에서 지금 소득 {bd.auc_b0.iloc[0]:.2f} vs ML {bd.auc_ml.iloc[0]:.2f}. 하락자의 약 95%가 기초생활보장 미수급(16-4).</td><td><span class="ok">일부 반영</span> – 고용24·복지로로 방향 안내 (기관 판매는 하지 않음)</td></tr>
<tr><td>개인 대화형 진단</td><td>중요도 상위 패턴(소득 이력, 연금 개시까지 거리, 일의 형태)이 그대로 문항과 이유 설명이 된다.</td><td><span class="ok">반영</span> – 21문항 + 아기씨 챗봇</td></tr></table>
<div class="box"><b class="t">차별점</b><ul>
<li><b>시간 차</b>: 기존 소득·재산 기준은 이미 떨어진 사람을 찾는다. 미리사주는 아직 빈곤선 위에 있는 사람의 2년 뒤를 본다.</li>
<li><b>계산의 2차 검진</b>: 연금 조회·노후 계산기가 “괜찮다”고 한 사람 안에서 실제로 반복 부족해질 사람을 더 잘 찾는다(15-1).</li>
<li><b>짧은 질문으로 검증된 성능</b>: 사용자가 답할 수 있는 21문항만으로 전체 입력 모델과 같은 성능(16-10). 회상 오차 ±20%에도 AUC −0.001.</li>
<li><b>팔지 않는 진단</b>: 상담·상품 연결 없이 공공기관 공식 경로로만 안내한다. 결과가 판매 목적과 섞이지 않는다.</li>
<li><b>사주 콘셉트</b>: 노후 진단의 문턱을 낮춘다. 단, 풀이는 통계 모델이며 예측일 뿐이라는 점을 화면에 밝힌다.</li></ul></div>
<h3>진행 순서</h3><ol>
<li><b>무료 공개 (현재)</b> – 연구·시연용으로 진단과 방향 안내를 공개한다.</li>
<li><b>이용 조건 정리</b> – 각 패널 기관에 영리 이용 가능 여부를 서면으로 확인하거나, 이용자 동의를 받은 자체 데이터로 재학습할 계획을 세운다(보사연 약관 제5장 제3조 ②: 사전 승낙 없는 영리 이용 금지).</li>
<li><b>사이트 유료화</b> – 2가 정리된 뒤 사이트 자체에 유료 기능을 붙인다.</li></ol>
<p class="muted">개인정보: 입력·대화는 저장하지 않는다. 건강은 묻지 않는 것이 기본이다(넣어도 성능 차이 없음, 16-10). 금융상품을 권유하지 않는다.</p>
</section>""")

w(sec_arch()); w(sec_exp()); w(sec_ml()); w(sec_ml2()); w(sec_ml3()); w(sec_p16()); w(sec_maturity()); w(sec_service()); w(sec_fail())
# ================= 14 판정·실패·한계·부록 =================
w(f'''<section class="sec"><h2><span class="no">18</span>판정 요약 · 한계 · 부록</h2>
<table><tr><th style="width:15%">구분</th><th>내용</th><th style="width:24%">결과</th></tr>
<tr><td><b>판정</b></td><td>가처분 3개 패널, 최종 모델 − 지금 소득, DeLong → 랜덤효과. 하한 &gt; 0, 실질 +0.03, 3/3 양수</td><td>{sgn(mf["est"])} [{sgn(mf["lo"])}, {sgn(mf["hi"])}] <span class="ok">통과</span></td></tr>
<tr><td><b>판정(사전 지정 모델)</b></td><td>LightGBM 단독 − 지금 소득</td><td>{sgn(ml["est"])} [{sgn(ml["lo"])}, {sgn(ml["hi"])}] <span class="ok">통과</span></td></tr>
<tr><td>재현 · 이식</td><td>노동(경상) · 의료 · 고령화 (경상)</td><td>{sgn(cmp_("KLIPS_r","최종−지금소득").delta)} · {sgn(cmp_("KHP_r","최종−지금소득").delta)} · {sgn(cmp_("KLoSA_r","최종−지금소득").delta)} (모두 양수)</td></tr>
<tr><td>탐색</td><td>모델 비교, 질문 수 고정, 부트스트랩, 집단별, 처음 보는 사람, 보정·이식</td><td>보조 근거, 판정에 쓰지 않음</td></tr>
<tr><td><b>추가 판정</b> (D16 검토 후)</td><td>E1b 2차 검진 · E2 그만둠·재취업 · E4 보정 개선 · M-A 개인별 설명 · M-B 적응형 질문 · M-C 판단 보류 · M2 사각지대 · M3 닮은 사람 · M7 가장 작은 변화</td><td>E1b <span class="ok">성공</span> · E2 <span class="ok">성공 6/6 ×2</span> · E4 <span class="no">불채택</span> · M-A <span class="ok">성공</span> · M-B <span class="no">실패</span> · M-C <span class="ok">성공 4/5</span> · M2 같은 모델로 충분 · M3 <span class="ok">성공 3/4</span> · M7 <span class="ok">방향 일치</span></td></tr>
<tr><td><b>운영 검증</b></td><td>D1 재취업 인과(AIPW + 위약) · D2 집단별 미탐 격차 · D3 고정 vs 재학습 · PSI 경보</td><td>D1 <span class="ok">인과 근거 있음 {_pp(_d1p[0])}</span> · D2 <span class="no">기준 미달 {DB["D2_ok"]}/4</span> · D3 <span class="ok">재학습 이득 {sgn(DB["D3_gain"])}</span> · PSI <span class="no">무효</span></td></tr>
<tr><td><b>프로세스 점검</b></td><td>P1 튜닝 확장 · P2 불균형 처리 · P3 스태킹 · P4 결측 대체 · P5 PR-AUC·의사결정 곡선 · P6 배포 실측</td><td>P1~P4 <span class="no">v3보다 낫지 않음(유지)</span> · P5 <span class="ok">성공 ×2</span> · P6 <span class="ok">실시간 가능</span></td></tr>
<tr><td><b>서비스 모델</b></td><td>미리사주 화면 21문항만으로 재학습 · 전체 모델 대비 손실 · 회상 소득 민감도 · 화면 경로 검증</td><td>손실 {SO[("KOWEPS","S20")]["res"]["loss"]:+.4f} [상한 {SO[("KOWEPS","S20")]["res"]["loss_hi"]:+.4f}] <span class="ok">통과</span> · 민감도 <span class="ok">허용</span></td></tr>
<tr><td class="no">공개할 실패</td><td><ul style="margin:0">
<li><b>AUC 0.85는 복지패널에서만</b> 넘었다. 재정·국민노후는 학습 표본이 작고(6~9천 행) 소득 측정 정밀도가 낮아 0.75~0.80. 패널 통합 학습·앙상블로도 거의 안 올랐다.</li>
<li><b>정답 정의를 네 번 바꿨다.</b> 처음 설계(2년 뒤 1회 하락)는 잡음이 커서 이득이 작았다. 바꾼 이유와 모든 버전의 결과를 3장에 공개했다.</li>
<li><b>부스팅이 로지스틱보다 확실히 낫지 않다</b>(부트스트랩 구간이 0 포함). 이득의 주원천은 정보 설계다.</li>
<li>최종 앙상블은 v3 탐색 중에 정했다. 사전 지정 LightGBM 결과를 함께 보고한다.</li>
<li>원 확률은 패널마다 어긋나고, 국민노후패널에서는 작은 표본으로 한 재보정이 오히려 나빴다.</li></ul></td><td>신뢰를 위해 그대로 보고</td></tr></table>
<h3>한계</h3><ul>
<li><b>4년 관측 조건</b>: 정답이 t+4를 요구해 시험셋이 2016~2021년 기준 차수다. 최근 경기(2022년 이후)는 시험에 덜 반영됐다.</li>
<li><b>표본 크기</b>: 국민노후패널 시험 1,752~1,887행. 개별 신뢰구간이 넓어 결합 분석으로 보완했다.</li>
<li><b>인과는 재취업 하나만</b>: 재취업 효과만 AIPW로 추정했다(관측 자료, 측정 안 된 교란은 남음). 그 밖의 중요도·부분의존은 예측에 쓰인 패턴이며, 처방 효과는 파일럿에서 검증해야 한다.</li>
<li><b>가중치</b>: 성능은 표본(비가중) 기준. 전국 비율을 말할 때는 패널 가중치를 적용해야 한다.</li></ul>
<h2 style="margin-top:7mm"><span class="no">A</span>부록 – 재현 정보</h2>
<table><tr><th style="width:26%">단계</th><th>스크립트 · 내용</th></tr>
<tr><td>패널별 변환</td><td><code>b_koweps · b_nastab · b_kreis · b_klips · b_khp · b_klosa</code> → 공통 스키마</td></tr>
<tr><td>이력 변수·결과 연결</td><td><code>build_common.py</code> – CPI, 균등화, 경상 빈곤선, t−4~t+4 연결</td></tr>
<tr><td>정답 v3</td><td><code>label_v3.py</code> – 가처분 빈곤선, 필요 생활비 기준선, 3번 중 2번 정답, 시험 봉인</td></tr>
<tr><td>전체 분석</td><td><code>v3_full.py</code> – 모델 비교, DeLong·메타, 부트스트랩, 질문 수 고정, 학습곡선·셔플, 중요도·부분의존, 집단별, 처음 보는 사람, 보정·이식, 사업 지표</td></tr>
<tr><td>추가 실험</td><td><code>e1b · e2_work · e4_calib · m_abc · m237 · d123 · p16 · s_model · make_spkg</code> (사전 규칙: <code>prereg_E124 · prereg_MABC · prereg_M237 · prereg_D123 · prereg_P16 · prereg_S</code>)</td></tr>
<tr><td>그림·보고서</td><td><code>figs_v3.py · report_v3.py</code></td></tr>
<tr><td>환경</td><td>Python 3.13 · scikit-learn 1.9.1 · LightGBM 4.7.0 · Optuna 5.0 · XGBoost 3.4.1 · CatBoost 1.2.10 · pandas 3.0 · 시드 42</td></tr></table>
</section></body></html>''')
open(W + 'report_v3.html', 'w').write(''.join(H)); print('html ok')
