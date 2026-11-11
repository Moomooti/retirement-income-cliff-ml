# report_v3.py 에 삽입되는 추가 장들 (exec로 불러 씀)
E1 = pickle.load(open(W + 'e1_out.pkl', 'rb')); E1b = pickle.load(open(W + 'e1b_out.pkl', 'rb'))
E2 = pickle.load(open(W + 'e2_out.pkl', 'rb')); E4 = pickle.load(open(W + 'e4_out.pkl', 'rb'))
MA_ = pickle.load(open(W + 'mabc_out_AC.pkl', 'rb')); MB_ = pickle.load(open(W + 'mabc_out_B.pkl', 'rb'))
R1b = E1b['R']; O12 = R1b[R1b.origin.isin(['O1', 'O2'])]
lift1b = lambda r, q: r[f'ml{q}'] / r[f'calc{q}'] - 1
E2s = E2['summ']; E2R = E2['R']
t1, t2 = E2s['T1 그만둠'], E2s['T2 재취업']
MAa, MAc, MBb = MA_['A'], MA_['C'], MB_['B']


def sec_feedback():
    return f'''<section class="sec"><h2><span class="no">0-1</span>받은 피드백과 예상 질문에 대한 답</h2>
<p>한 줄 답 → 근거 숫자 → 자세한 장 순서로 정리했다.</p>
<table><tr><th style="width:20%">질문</th><th style="width:32%">한 줄 답</th><th>근거 (모두 봉인 시험)</th><th style="width:8%">장</th></tr>
<tr><td><b>① 국민연금 조회·은행 노후 계산기와 뭐가 다르냐</b><br><span class="muted">받은 피드백</span></td><td>계산을 대체하지 않는다. 계산이 “괜찮다”고 한 사람 중 실제로 반복 부족해질 사람을 찾는 <b>2차 검진</b>이다.</td>
<td>계산상 괜찮은 사람 안에서 충족률 AUC {f3(O12.auc_calc.min())}~{f3(O12.auc_calc.max())} vs ML {f3(O12.auc_ml.min())}~{f3(O12.auc_ml.max())}. 같은 인원(상위 10%) 상담 시 부족자 {pct(lift1b(O12.iloc[0], 10), 0)}~{pct(lift1b(O12.iloc[1], 10), 0)} 더 발견. ML 상위 10%의 실제 반복 부족률 {pct(O12["rate_상위 10%"].min(), 0)}~{pct(O12["rate_상위 10%"].max(), 0)} vs 나머지 70% {pct(O12["rate_나머지 70%"].min(), 0)}~{pct(O12["rate_나머지 70%"].max(), 0)}</td><td>15-1</td></tr>
<tr><td><b>② 핵심 모델(M1)이 기존 서비스와 비슷하다</b><br><span class="muted">받은 피드백</span></td><td>M1은 “지금 부족한가”에 가까운 질문이라 기존 계산과 같아 보였다. 이번 모델은 질문을 “지금은 괜찮은데 앞으로 반복 부족”으로 바꿨다.</td>
<td>같은 데이터에서 상태형 정답은 지금 소득만으로 {f3(J[1][1])}(ML 이득 {sgn(J[1][2]-J[1][1])}), 이번 정답은 {f3(J[3][1])}(이득 {sgn(J[3][2]-J[3][1])}). 기존 서비스가 이미 아는 사람이 아니라 못 보는 사람을 맞힌다</td><td>3, 15-1</td></tr>
<tr><td><b>③ 왜 ML이어야 하냐</b><br><span class="muted">받은 피드백</span></td><td>사람이 정한 계산식이 아니라 <b>실제 결과로 학습한 가중치·질문·패턴</b>이 미래 사람에게서 더 잘 맞았다. 일 전환 문제에서는 부스팅이 로지스틱보다도 유의하게 높다.</td>
<td>계산기형 대비: 소득 하락 {sgn(mc["est"])}, 그만둠 {sgn(t1["meta_calc"]["est"])}, 재취업 {sgn(t2["meta_calc"]["est"])}(6/6 조사 통과). 로지스틱 대비 LightGBM: 그만둠 {sgn(t1["meta_lr"]["est"])} [{sgn(t1["meta_lr"]["lo"])}, {sgn(t1["meta_lr"]["hi"])}], 재취업 {sgn(t2["meta_lr"]["est"])}. 질문 12개 고정 시 ML 선택 &gt; 전문가 양식. 개인별 이유·적응형 질문·판단 보류는 ML만 할 수 있는 기능</td><td>6, 8, 15-2, 16</td></tr>
<tr><td><b>④ 표본이 작다</b><br><span class="muted">예상 질문</span></td><td>사람×차수 단위로 학습 {n_tr_all:,}행·시험 {n_te_all:,}행. 신뢰구간도 사람 단위로 보수적으로 구했다.</td>
<td>판정 3개 패널 결합 표준오차 {mf["se"]:.3f} → +0.03 차이 검출 가능. 사람 단위 부트스트랩으로도 결론 유지({sgn(BM["최종−지금소득"]["est"])}, 하한 {sgn(BM["최종−지금소득"]["lo"])})</td><td>4, 7</td></tr>
<tr><td><b>⑤ AUC가 낮다</b><br><span class="muted">예상 질문</span></td><td>0.9는 지금 소득이 다 맞히는 쉬운 정답에서만 나온다. 이 문제의 천장은 약 0.80이고, 가처분소득이 정교한 복지패널은 {f3(auc("KOWEPS_r", FIN))}.</td>
<td>AUC 대신 현장 지표: 같은 상담 인원으로 하락자 +18~32%(과제별). 15종 모델이 모두 같은 높이에서 멈춤 = 데이터의 신호를 다 뽑았다는 신호</td><td>3, 6, 13</td></tr>
<tr><td><b>⑦ 서비스가 복잡하다</b><br><span class="muted">예상 질문</span></td><td>제품은 하나다: 미리사주 웹사이트. 21문항 → 위험 구간 · 이유 3가지 · 판단 보류 → 방향과 공식 사이트. 상담·상품 판매는 하지 않는다.</td>
<td>기술 설계도 한 장으로 정리. 21문항만으로 전체 입력 모델과 같은 성능(손실 +0.001, 16-10). 사람마다 질문을 바꾸는 적응형 질문은 큰 패널에서만 통해 다음 단계로 둠(16-2)</td><td>13, 13-1, 16-10</td></tr></table>
</section>'''


SOa = pickle.load(open(W + 's_out.pkl', 'rb'))[('KOWEPS', 'S20')]['res']


def sec_arch():
    r = SOa
    return f"""<section class="sec"><h2><span class="no">13-1</span>기술 설계도 – 미리사주 한 장</h2>
<p>웹 화면 하나, 서버 하나, 검증된 모델 하나다. 숫자는 역할을 나눈다: <b>ML은 위험 구간·이유·판단 보류</b>, <b>계산 풀이는 사용자가 넣은 금액의 단순 계산</b>, 대화 AI(아기씨)는 문장만 만들고 숫자를 만들지 않는다.</p>
<div style="border:1px solid var(--rule);border-radius:3mm;padding:3.5mm;margin:2mm 0 4mm">
<div style="font-size:7.6pt;color:var(--ink3);font-weight:700;margin-bottom:1.5mm">① 입력 (미리사주 웹)</div>
<div class="flow" style="grid-template-columns:repeat(3,1fr);margin:0 0 2mm">
 <div class="c"><b>네 기둥 21문항</b>본인 또는 부모님 대신<br>생년·가족 / 연금 / 소득 흐름 / 일과 재산</div>
 <div class="c"><b>선택: 은퇴 계획</b>은퇴 나이·국민연금 예상액 등<br>계산 풀이에만 사용 (모델에 안 보냄)</div>
 <div class="c"><b>아기씨에게 묻기</b>노후 소득·연금·제도 질문<br>저장하지 않음</div></div>
<div class="arrow">↓</div>
<div style="font-size:7.6pt;color:var(--ink3);font-weight:700;margin-bottom:1.5mm">② 변수 만들기 (predict.py, 학습 때와 같은 정의)</div>
<div class="pipe" style="margin:0 0 2mm"><div class="s"><b>소득 척도</b>월×12 · CPI 실질화 · ÷√가구원 · ÷그해 빈곤선</div><div class="a">→</div><div class="s"><b>이력 변수</b>지금·1년 전·2년 전 변화 · 최저 · 출렁임</div><div class="a">→</div><div class="s"><b>재산</b>2025년 물가 · 소득 대비 배수 · 사는 집 포함</div><div class="a">→</div><div class="s"><b>대상 판정</b>50~69세 · 지금 빈곤선 이상</div></div>
<div class="arrow">↓</div>
<div style="font-size:7.6pt;color:var(--ink3);font-weight:700;margin-bottom:1.5mm">③ ML 코어 (서비스 모델, 16-10)</div>
<div class="flow" style="grid-template-columns:repeat(3,1fr);margin:0 0 2mm">
 <div class="c main"><b>지속 소득 하락</b>LightGBM + 로지스틱 순위 결합<br>시험 AUC {r["auc_service"]:.3f} · 전체 모델 대비 손실 {r["loss"]:+.3f}</div>
 <div class="c main"><b>개인별 이유</b>TreeSHAP 기여 상위 3개<br>“위험을 올림 / 낮춤”으로 표시</div>
 <div class="c main"><b>판단 보류</b>클래스별 컨포멀 (α = 0.10)<br>포함률 {r["cov_pos"]:.1%} / {r["cov_neg"]:.1%}</div></div>
<div class="arrow">↓</div>
<div style="font-size:7.6pt;color:var(--ink3);font-weight:700;margin-bottom:1.5mm">④ 풀이 · 안내 (ML 바깥)</div>
<div class="pipe" style="margin:0 0 2mm"><div class="s"><b>위험 구간</b>상위 20% / 20~40% / 그 밖 (+ 판단 보류)</div><div class="a">+</div><div class="s"><b>계산 풀이</b>선택 입력이 있으면 공백기·은퇴 후 월수입·빚 부담</div><div class="a">+</div><div class="s"><b>방향 안내</b>이유 → 확인할 제도 → 공식 사이트 (13장 표)</div><div class="a">+</div><div class="s"><b>아기씨 문장</b>Claude API, 숫자 생성 금지·겁주기 금지</div></div>
<div class="arrow">↓</div>
<div style="font-size:7.6pt;color:var(--ink3);font-weight:700;margin-bottom:1.5mm">⑤ 배포</div>
<div class="flow" style="grid-template-columns:repeat(3,1fr);margin:0">
 <div class="c repl"><b>웹: GitHub Pages</b>index.html 한 장 · 외부 JS 없음<br>입력값 브라우저에도 저장 안 함</div>
 <div class="c repl" style="border-width:2px"><b>서버: Render (FastAPI)</b>/predict · /chat · /health<br>API 키는 서버 환경변수에만 · 요청 제한</div>
 <div class="c repl"><b>저장: 없음</b>요청 본문·대화 로그 미저장<br>모델 파일과 집계 상수만 배포</div></div>
<div style="margin-top:2.5mm;font-size:7.8pt;color:var(--ink2);border-top:1px dashed var(--rule);padding-top:2mm"><b>운영 루프</b> – 새 조사 차수가 나오면 연 1회 정기 재학습(D3: 재학습 +0.022, 분포 이동 경보는 무효) → 같은 봉인 시험·일치 테스트 통과 시에만 교체. 검증은 했지만 서비스에 싣지 않은 것: 그만둠·재취업 모델(15-2), 닮은 30명(16-5), 가장 작은 변화(16-6), 적응형 질문(16-2).</div>
</div>
<div class="box"><b class="t">첫 제품(MVP) 한 장</b>
<b>사용자</b> 50~69세 본인 · 부모님 대신 진단하는 자녀 &nbsp;|&nbsp; <b>입력</b> 21문항(건강은 묻지 않음) &nbsp;|&nbsp; <b>출력</b> 위험 구간 + 이유 3가지 + 판단 보류 + 방향·공식 사이트 &nbsp;|&nbsp; <b>성과 지표(제안)</b> 진단 완료 수, 공식 사이트로 이동한 비율 &nbsp;|&nbsp; <b>과금</b> 현재 무료, 향후 사이트 유료화(미정)</div>
</section>"""


def sec_exp():
    r1 = ''.join(f'<tr><td>{r.origin}</td><td class="n">{r.years}</td><td class="n">{int(r.n_te):,}</td><td class="n">{pct(r.rate)}</td><td class="n">{f3(r.auc_calc)}</td><td class="n"><b>{f3(r.auc_ml)}</b></td><td class="n">{int(r.calc10)} → <b>{int(r.ml10)}</b></td><td class="n">{int(r.calc20)} → <b>{int(r.ml20)}</b></td><td class="n">{pct(r["rate_상위 10%"])}</td><td class="n">{pct(r["rate_10~30%"])}</td><td class="n">{pct(r["rate_나머지 70%"])}</td></tr>' for _, r in R1b.iterrows())
    Q = E1['Q']
    q1 = ''.join(f'<tr><td>{r.calc}</td><td>{r.tier}</td><td class="n">{int(r.n):,}</td><td class="n">{pct(r.rate)}</td><td class="n">[{pct(r.lo)}, {pct(r.hi)}]</td></tr>' for _, r in Q.iterrows())
    r2 = ''.join(f'<tr><td>{r.label}</td><td>{NAME[r.panel]}</td><td class="n">{int(r.n_te):,}</td><td class="n">{pct(r.rate_te)}</td><td class="n">{f3(r.auc_calc)}</td><td class="n">{f3(r.auc_lr)}</td><td class="n"><b>{f3(r.auc_lgb)}</b></td><td class="n">{sgn(r.d_calc)} <span class="muted">[{sgn(r.lo_calc)}]</span></td><td class="n">{sgn(r.d_lr)}</td><td>{r.status}</td></tr>' for _, r in E2R.iterrows())
    e4 = E4['R'].pivot(index='task', columns='method', values='ece') * 100
    r4 = ''.join(f'<tr><td>{TN[k]}</td>' + ''.join(f'<td class="n">{v:.2f}%p</td>' for v in e4.loc[k]) + '</tr>' for k in e4.index)
    return f'''<section class="sec"><h2><span class="no">15</span>추가 실험 (D16 검토 후) – E1 · E1b · E2 · E4</h2>
<p>D16 보고서를 검토해 우리 서비스에 없던 요소를 골라, 넣기 전에 실험으로 검증했다. 판정 규칙은 실행 전에 파일로 고정했다(prereg_E124.txt).</p>
<h3>15-1. 노후 계산의 2차 검진 (국민노후보장패널)</h3>
<p><b>E1 (규칙상 성공, 설계 실수 발견)</b> – 계산 가능자 전체로 위험 구간 경계를 정했다. 계산 × ML 위험 표는 아래와 같고 판정 규칙은 통과했지만, 계산상 괜찮은 집단의 “높음”이 {int(Q[(Q.calc=="계산상 괜찮음")&(Q.tier=="높음")].n.iloc[0])}명뿐이었다.</p>
{table(["계산", "ML 위험", "인원", "실제 4년 반복 부족", "95% CI"], [q1], 'style="font-size:7.8pt"', num=[2, 3, 4])}
<p><b>E1b – E1 설계 실수 보완 (성공)</b>. 서비스는 계산상 괜찮은 사람 안에서 우선순위를 정하므로, 경계를 그 집단 기준(학습셋 교차 예측 점수 분위)으로 다시 정의했다. 판정은 처음 채점하는 두 시점(O1·O2)으로 하고, E1과 같은 시험셋(O3)은 참고로 보고한다.</p>
{table(["시점", "기준연도", "인원", "반복 부족", "충족률 AUC", "ML AUC", "상위 10% 찾은 수", "상위 20%", "ML 상위 10%", "10~30%", "나머지 70%"], [r1], 'style="font-size:7.4pt"')}
<div class="box"><b class="t">판정: 성공</b>모든 시점에서 ML이 충족률보다 더 많이 찾았다. 세 시점 합친 상위 20% 차이 +{int(E1b["est"])}명 [95%: +{int(E1b["lo"])} ~ +{int(E1b["hi"])}명, 사람 단위 부트스트랩 1,000회]. 구간별 실제 부족률이 모든 시점에서 상위 10% &gt; 10~30% &gt; 나머지 순서. 가장 오래된 시점(O1, 학습 3,472행)은 차이가 작고(+4~11%), 학습 데이터가 쌓일수록 커진다.</div>
</section>
<section class="sec"><h3>15-2. 일 전환 정답 – 그만둠(T1) · 재취업(T2) (6개 패널, 봉인 시험)</h3>
<p>D16 탐색에서 ML 이득이 가장 컸던 정답을 미래 차수 봉인 시험으로 확인했다. 비교: ① 계산기형(나이 + 지금 소득) ② 같은 입력 로지스틱 ③ LightGBM.</p>
{table(["정답", "패널", "시험", "발생률", "계산기형", "로지스틱", "LightGBM", "LGB − 계산기형 [하한]", "LGB − 로지스틱", "판정"], [r2], 'style="font-size:7.4pt"', num=[2, 3, 4, 5, 6, 7, 8])}
<div class="box"><b class="t">판정: T1·T2 모두 성공 (6/6 조사 통과, 기준 80%)</b>
계산기형 대비 결합: 그만둠 {sgn(t1["meta_calc"]["est"])} [{sgn(t1["meta_calc"]["lo"])}, {sgn(t1["meta_calc"]["hi"])}], 재취업 {sgn(t2["meta_calc"]["est"])} [{sgn(t2["meta_calc"]["lo"])}, {sgn(t2["meta_calc"]["hi"])}].
<b>같은 입력의 로지스틱 대비로도 LightGBM이 유의하게 높다</b>: 그만둠 {sgn(t1["meta_lr"]["est"])} [{sgn(t1["meta_lr"]["lo"])}, {sgn(t1["meta_lr"]["hi"])}], 재취업 {sgn(t2["meta_lr"]["est"])} [{sgn(t2["meta_lr"]["lo"])}, {sgn(t2["meta_lr"]["hi"])}]. 소득 하락에서는 차이가 없던 비선형 학습의 가치가 일 전환 문제에서는 드러난다. 재취업지원서비스에서 서비스 강도를 나누는 근거가 된다.</div>
<h3>15-3. 확률 보정 개선 (E4) – 실패, 불채택</h3>
{table(["과제", "A 원 확률", "B 마지막 연도 Platt(기존)", "C 교차 예측 Platt(신규)"], [r4], 'style="font-size:7.8pt"')}
<p>ECE(낮을수록 좋음). C가 가장 좋은 과제는 {E4["c_best"]}/5로 기준(4/5) 미달 → <b class="no">불채택</b>. 어느 한 방식도 모든 패널에서 낫지 않았다. 확률 대신 <b>순위 구간과 판단 보류(16-3)</b>로 말하는 것이 지금 데이터로 정직한 방법이다.</p>
</section>'''


def sec_ml():
    ra = ''.join(f'<tr><td>{TN[r.task]}</td><td class="n">{int(r.n):,}</td><td class="n">{r.ch_top:.3f}</td><td class="n">{r.ch_rnd:.3f}</td><td class="n"><b>{r.ratio:.1f}배</b></td><td class="n">{"<0.001" if r.p < 0.001 else f"{r.p:.3f}"}</td><td class="n">{f3(r.auc_full)} → {f3(r.auc_after_top3)}</td></tr>' for _, r in MAa.iterrows())
    AT = MA_['A_top']
    rt = ''.join(f'<tr><td>{TN[k]}</td><td style="font-size:7.6pt">{" · ".join(f"{LAB.get(r.feature, r.feature)} {r.share*100:.0f}%" for _, r in g.head(4).iterrows())}</td></tr>' for k, g in AT.groupby('task', sort=False))
    rb = ''.join(f'<tr><td>{TN[r.task]}</td><td class="n">{int(r.n):,}</td><td class="n">{f3(r.auc_b0)}</td><td class="n">{f3(r.auc_fixed12)}</td><td class="n"><b>{f3(r.auc_adaptive)}</b></td><td class="n">{f3(r.auc_all)}</td><td class="n"><b>{r.q_mean:.1f}</b></td><td class="n">{r.q_median:.0f} / {r.q_p90:.0f}</td><td class="n">{int(r.n_feat)}</td></tr>' for _, r in MBb.iterrows())
    rc = ''.join(f'<tr><td>{TN[r.task]}</td><td class="n">{pct(r.cov_pos)}</td><td class="n">{pct(r.cov_neg)}</td><td class="n">{pct(r.risk_only)}</td><td class="n">{pct(r.safe_only)}</td><td class="n">{pct(r.abstain)}</td><td class="n"><b>{pct(r.fall_in_risk)}</b></td><td class="n"><b>{pct(r.fall_in_safe)}</b></td><td class="n">{pct(r.base)}</td></tr>' for _, r in MAc.iterrows())
    return f'''<section class="sec"><h2><span class="no">16</span>머신러닝 확장 – ML만 할 수 있는 세 가지</h2>
<p>앞 장들은 “ML이 계산보다 잘 맞힌다”를 보였다. 이 장은 <b>계산식으로는 원리상 할 수 없는 일</b>을 세 가지 실험으로 검증한다. 판정 규칙은 실행 전에 고정했다(prereg_MABC.txt).</p>
<h3>16-1. 개인별 설명 – “왜 이 사람이 위험한가” (M-A, {MA_["A_verdict"]})</h3>
<div class="def"><b>TreeSHAP 기여도</b> – 한 사람의 예측 점수(로그 오즈)를 “기준값 + 변수별 기여”의 합으로 정확히 쪼개는 방법. 기여가 큰 변수가 그 사람의 위험 이유다.<br>예: 기준값 −2.5 + 지금 소득 +0.9 + 최근 4년 최저 소득 +0.6 + 연금 개시까지 거리 +0.3 … = 그 사람의 점수.</div>
<p><b>충실도 시험</b>: 설명이 그럴듯하기만 한지, 모델이 실제로 그 변수에 기대는지 확인했다. 각 사람의 “위험을 올린 상위 3개 변수”를 학습셋 중앙값으로 바꿨을 때의 예측 변화를 무작위 3개를 바꿨을 때와 비교했다.</p>
{table(["과제", "시험 인원", "상위 3개 제거 시 |변화|", "무작위 3개", "배수", "p (윌콕슨)", "AUC: 원래 → 상위 3개 제거"], [ra], 'style="font-size:7.6pt"')}
<p>모든 과제에서 상위 3개를 지웠을 때 예측이 무작위보다 {MAa.ratio.min():.1f}~{MAa.ratio.max():.1f}배 크게 바뀌고, AUC도 크게 떨어진다. 설명이 모델의 실제 판단 근거라는 뜻이다. 대화형 진단의 “이유 3가지”를 이 값으로 만든다.</p>
<h3>위험 상위 20%에서 가장 자주 1순위 이유가 된 변수</h3>{table(["과제", "1순위 이유 비율 (상위 4개)"], [rt], num=[])}
</section>
<section class="sec"><h3>16-2. 적응형 질문 – 사람마다 다른 질문 경로 (M-B, {MB_["B_verdict"]})</h3>
<p>고정 설문은 모두에게 같은 질문을 같은 순서로 묻는다. 적응형 질문은 지금까지의 답을 보고 <b>이 사람에게 가장 정보가 많은 다음 질문</b>을 모델이 고르고, 더 물어도 예측이 거의 바뀌지 않으면 멈춘다.</p>
<div class="def"><b>정보 가치</b> – 아직 묻지 않은 질문에 가능한 답 10개를 넣어 봤을 때 예측 확률이 얼마나 흔들리는지(표준편차). 많이 흔들릴수록 그 질문의 답이 판단을 바꾼다. 최대 정보 가치가 1%p 미만이면 멈춘다.</div>
<p>진단 모델은 일부 항목이 비어 있어도 예측하도록, 학습행을 무작위로 가려서 함께 학습했다. 같은 진단 모델로 고정 12문항(내부 검증 중요도 순)·전체 질문과 비교했다(시험셋 과제당 최대 1,500명).</p>
{table(["과제", "평가 인원", "지금 소득만", "고정 12문항", "적응형", "전체 질문", "평균 질문 수", "중앙값 / 90%", "전체 질문 수"], [rb], 'style="font-size:7.6pt"')}
<p>판정: 적응형이 고정 12문항보다 0.005 이상 떨어지지 않으면서 평균 질문 수가 12개 미만인 과제 {MB_["B_ok"]}/5 → <b class="no">{MB_["B_verdict"]}</b>(기준 4/5).
학습 데이터가 큰 복지·재정에서는 <b>더 적은 질문(평균 7.4·10.8개)으로 고정 12문항과 같거나 높았다</b>. 반면 국민노후(학습 6~7천 행)에서는 질문을 아낀 만큼 0.011~0.018 떨어졌고, 노동은 경계에서 미달(−0.005)했다. 정보 가치 추정이 작은 표본에서는 불안정하다는 뜻이다.
그래서 서비스 진단은 <b>고정 문항(미리사주 21문항)</b>으로 하고, 적응형 질문은 진단 데이터가 쌓인 뒤 다시 검증하는 다음 단계로 둔다.</p>
<h3>16-3. 판단 보류가 있는 예측 – “모르면 모른다고 말한다” (M-C, {MA_["C_verdict"]})</h3>
<div class="def"><b>conformal 예측</b> – 보정용 자료에서 “틀릴 확률이 α 이하가 되는” 점수 경계를 구해, 각 사람에게 {{위험}}, {{안전}}, {{위험, 안전}} 중 하나를 준다. 마지막은 판단 보류다. 확률 보정(E4)이 실패해도, 실제 하락자의 90%가 “위험”을 포함한 판정을 받도록 경계를 정할 수 있다.</div>
{table(["과제", "하락자 중 ‘위험’ 포함", "비하락자 중 ‘안전’ 포함", "위험 단독", "안전 단독", "판단 보류", "위험 단독 중 실제 하락", "안전 단독 중 실제 하락", "기본 하락률"], [rc], 'style="font-size:7.4pt"')}
<p>판정: 두 포함률이 모두 88% 이상인 과제 {MA_["C_ok"]}/5 → <b>{MA_["C_verdict"]}</b>(노동패널은 비하락자 포함률 {pct(MAc[MAc.task=="KLIPS_r"].cov_neg.iloc[0])}로 미달). 학습기간과 시험기간이 달라도 보장이 거의 유지됐다.
현장 의미: “안전”으로 단독 판정된 사람의 실제 하락률은 {pct(MAc.fall_in_safe.min())}~{pct(MAc.fall_in_safe.max())}로 기본 하락률의 1/3~1/5다. 이 사람들은 2년 뒤 재점검으로 충분하고, 상담 자원은 “위험”(실제 하락 {pct(MAc.fall_in_risk.min())}~{pct(MAc.fall_in_risk.max())})과 “판단 보류”에 쓴다. 판단 보류 비율이 패널마다 26~70%로 큰 것은 이 문제의 어려움을 그대로 드러낸 것이고, 그 사람들은 적응형 질문으로 더 묻는 대상이 된다.</p>
</section>'''


def sec_fail():
    return f'''<section class="sec"><h2><span class="no">17</span>실패 기록 (참고)</h2>
<p>결과가 좋지 않았거나 계획대로 되지 않은 것을 모두 모았다. 판정에서 지운 것은 없다.</p>
<table><tr><th style="width:4%">#</th><th style="width:22%">무엇</th><th>무슨 일이 있었나</th><th style="width:26%">어떻게 처리했나</th></tr>
<tr><td>1</td><td>정답 v1 (2년 뒤 1회 하락)</td><td>빈곤선 근처의 한 해 출렁임이 정답에 섞여 잡음이 컸다. ML 이득 +{J[0][2]-J[0][1]:.3f}에 그침</td><td>반복 관측 정답(3번 중 2번)으로 교체 → 이득 +{J[3][2]-J[3][1]:.3f}</td></tr>
<tr><td>2</td><td>상태형 정답 (M1 방식)</td><td>AUC {f3(J[1][2])}로 높았지만 지금 소득만으로 {f3(J[1][1])}. 기존 서비스와 같은 질문</td><td>비교용으로만 남김</td></tr>
<tr><td>3</td><td>AUC 0.85 목표</td><td>복지패널({f3(auc("KOWEPS_r", FIN))})만 달성. 재정·국민노후 0.75~0.80. 패널 통합·앙상블로도 거의 안 오름</td><td>현장 지표(같은 인원 발견 수)로 말함</td></tr>
<tr><td>4</td><td>v1 사전 지정 HGB</td><td>같은 입력의 로지스틱보다 0.010 낮았다(설정 문제)</td><td>v3는 LightGBM으로 사전 지정, 원인 공개</td></tr>
<tr><td>5</td><td>소득 하락에서 부스팅 ≈ 로지스틱</td><td>LightGBM − 로지스틱 {sgn(BM["LightGBM−로지스틱"]["est"])} (0 포함)</td><td>일 전환 문제에서 부스팅 우위 확인(15-2), 최종 모델은 두 모델 앙상블</td></tr>
<tr><td>6</td><td>E1 설계 실수</td><td>위험 구간 경계를 계산 가능자 전체로 정해 계산상 괜찮은 집단의 “높음”이 10명뿐</td><td>E1b로 보완, 처음 채점한 두 시점으로 판정(성공)</td></tr>
<tr><td>7</td><td>E4 확률 보정 개선</td><td>새 방식이 5개 중 1개에서만 최선 → 불채택. 국민노후패널은 기존 재보정이 오히려 악화(1.5 → 4.6%p)</td><td>확률 대신 순위 구간 + 판단 보류(16-3)로 말함</td></tr>
<tr><td>8</td><td>M-C 노동패널</td><td>비하락자 포함률 {pct(MAc[MAc.task=="KLIPS_r"].cov_neg.iloc[0])}로 기준(88%) 미달</td><td>4/5 통과로 판정은 성공, 미달 공개</td></tr>
<tr><td>9</td><td>이식 – 국민노후</td><td>다른 패널에서 학습한 공통 입력 모델은 국민노후에서 0.68~0.73</td><td>국민노후는 자체 추가 입력과 함께 사용</td></tr>
<tr><td>10</td><td>패널 합쳐 학습</td><td>합쳐도 이득 없음(D16과 같은 결론)</td><td>패널별 학습 + 결합 메타분석 유지</td></tr>
<tr><td>11</td><td>M-B 적응형 질문</td><td>5개 중 2개 과제에서만 통과(기준 4/5). 국민노후에서 0.011~0.018 하락</td><td>서비스는 고정 21문항, 적응형은 다음 단계</td></tr>
<tr><td>12</td><td>M2 사각지대 별도 모듈</td><td>2단계·직접 학습 모두 지속 하락 모델보다 나아지지 않음(+0.000~0.002)</td><td>지속 하락자의 95%가 미수급 → 같은 점수를 사각지대 발굴에 그대로 사용</td></tr>
<tr><td>13</td><td>M3 국민노후</td><td>닮은 30명 비율이 지금 소득보다 +0.008(기준 +0.02 미달)</td><td>국민노후에서는 사례형 설명을 쓰지 않음</td></tr>
<tr><td>14</td><td>M7 바꿀 수 있는 위험</td><td>위험 상위 20% 중 행동 1~2개로 벗어나는 사람은 4~18%뿐. 재정패널은 재취업 방향 차이 없음</td><td>채우기 계획은 제도 연결을 먼저, 반사실은 예측으로만 표시</td></tr>
<tr><td>15</td><td>D2 공정성</td><td>집단 간 미탐률 격차가 지금 소득보다 커짐(통과 {DB["D2_ok"]}/4, 기준 3/4). 취약 집단 미탐은 크게 줄고 50대·대졸·취업자는 그대로</td><td>집단별 미탐·오탐표 공개, 변화가 생기면 재진단 안내</td></tr>
<tr><td>16</td><td>D3 PSI 경보</td><td>분포 이동과 성능 차이 상관 {DB["D3_rho"]:.2f}(기준 0.5)</td><td>경보 대신 매년 정기 재학습</td></tr>
<tr><td>17</td><td>D1 국민노후 겹침</td><td>재취업자 9%라 성향 점수 겹침 44%만 유지, 개별 추정 불안정</td><td>4개 패널 결합으로만 판정</td></tr>
<tr><td>18</td><td>P1·P2·P3·P4 표준 기법</td><td>튜닝 확장·불균형 처리·스태킹·결측 대체 모두 v3보다 유의하게 낫지 않음. 불균형 처리는 확률을 크게 부풀림</td><td>v3 유지. 성능 천장이 정보의 한계라는 근거로 사용</td></tr>
<tr><td>19</td><td>실행 중 오류</td><td>패키지 저장소 차단(프록시 지정으로 해제, Optuna 설치 포함), HistGB 빈 열 오류, 부분의존 문법 변경, 첫 부분의존 그림의 잘못된 해석 제목</td><td>모두 수정 후 전체 재실행, 그림 제목은 데이터 모양대로 다시 붙임</td></tr></table>
</section>'''

M23 = pickle.load(open(W + 'm237_out_M2M3.pkl', 'rb')); M7_ = pickle.load(open(W + 'm237_out_M7.pkl', 'rb'))
R2_, R3_, R7_, C7_, D7_ = M23['M2'], M23['M3'], M7_['M7'], M7_['M7_combos'], M7_['M7_dir']


def sec_ml2():
    r2 = ''.join(f'<tr><td>{NAME[r.panel]}</td><td class="n">{int(r.n_te):,}</td><td class="n">{pct(r.rate)}</td><td class="n"><b>{pct(r.share_norecv_among_fall)}</b></td><td class="n">{f3(r.auc_b0)}</td><td class="n">{f3(r.auc_v3)}</td><td class="n">{f3(r.auc_two)}</td><td class="n">{f3(r.auc_dir)}</td><td class="n">{sgn(r.d)} [{sgn(r.lo)}]</td></tr>' for _, r in R2_.iterrows())
    r3 = ''.join(f'<tr><td>{NAME[r.panel]}</td><td class="n">{int(r.n_te):,}</td><td class="n">{f3(r.auc_b0)}</td><td class="n"><b>{f3(r.auc_knn)}</b></td><td class="n">{f3(r.auc_lgb)}</td><td class="n">{r.rho:.2f}</td><td>{"통과" if (r.auc_knn >= r.auc_b0 + 0.02 and r.rho >= 0.6) else "미달"}</td></tr>' for _, r in R3_.iterrows())
    r7 = ''.join(f'<tr><td>{NAME[r.panel]}</td><td class="n">{int(r.n_high):,}</td><td style="font-size:7.2pt">{" · ".join(a.replace("금융자산 ", "자산").replace(",000만원", "천만") for a in r.actions)}</td><td class="n">{pct(r.share_one)}</td><td class="n"><b>{pct(r.share_any)}</b></td><td class="n">{r.model_delta_emp*100:+.1f}%p</td><td class="n">{D7_["per"][r.panel]*100:+.1f}%p</td></tr>' for _, r in R7_.iterrows())
    c7 = ''.join(f'<tr><td>{NAME[p]}</td><td style="font-size:7.6pt">{" · ".join(f"{x.change} {x.share*100:.1f}%" for _, x in g.head(4).iterrows())}</td></tr>' for p, g in C7_.groupby('panel', sort=False))
    return f'''<section class="sec"><h3>16-4. 사각지대 – 지속 하락했는데 기초생활보장도 못 받을 사람 (M2, {M23["M2_verdict"]})</h3>
<p>지자체 사각지대 발굴에 그대로 쓰일 정답이다. 재정패널(기초생활보장 수급 유무)과 노동패널(기초생활보호 이전소득)로 “지속 하락 + 그 기간 수급 없음”을 만들고, 별도 모델이 필요한지 시험했다.</p>
{table(["패널", "시험", "사각지대 비율", "지속 하락자 중 미수급", "지금 소득", "지속 하락 모델(v3)", "2단계(하락×미수급)", "직접 학습", "선택 모델 − v3 [하한]"], [r2], 'style="font-size:7.4pt"')}
<div class="box gray"><b class="t">판정: {M23["M2_verdict"]}</b>
지속 하락으로 떨어진 사람의 <b>{pct(R2_.share_norecv_among_fall.min())}~{pct(R2_.share_norecv_among_fall.max())}가 4년 동안 기초생활보장을 한 번도 받지 않았다.</b> 그래서 사각지대 정답이 지속 하락 정답과 거의 같고, 별도 모델(2단계·직접 학습)은 지속 하락 모델보다 나아지지 않았다(차이 +0.000~+0.002, 0 포함).
그래서 지속 하락 점수가 사각지대 신호도 겸한다. 미리사주는 위험이 높게 나오면 <b>복지로 복지서비스 모의계산</b>으로 안내한다(13장).</div>
<h3>16-5. 닮은 사람 – “나와 닮은 실제 30명은 어떻게 됐나” (M3, {M23["M3_verdict"]} {M23["M3_ok"]}/4)</h3>
<div class="def"><b>가중 맨해튼 KNN</b> – 입력을 표준화하고 변수마다 중요도(내부 검증 순열 중요도)를 곱한 뒤, 차이의 절댓값 합이 가장 작은 학습셋 사람 30명을 찾는다. 그 30명 중 실제로 지속 하락한 비율이 “닮은 사람의 결과”다.</div>
{table(["패널", "시험", "지금 소득", "닮은 30명 비율", "LightGBM", "LightGBM과 순위 상관", "판정"], [r3])}
<p>복지·재정·노동에서는 닮은 30명의 실제 결과만으로 지금 소득보다 0.02~0.04 높고, 최종 모델 점수와 순위 상관이 0.81~0.84다. 즉 숫자 기여도(16-1)와 함께 <b>“당신과 비슷한 30명 중 X명이 실제로 부족해졌다”</b>는 사례형 설명을 붙일 수 있다. 국민노후패널은 표본이 작아 기준(+0.02)에 못 미쳐 이 패널에서는 쓰지 않는다. 개인 기록은 보여주지 않고 30명 집계만 보여준다.</p>
</section>
<section class="sec"><h3>16-6. 가장 작은 변화 – “무엇을 바꾸면 위험 구간에서 벗어나나” (M7, {M7_["M7_verdict"]})</h3>
<div class="def"><b>제약 반사실 탐색</b> – 바꿀 수 있는 항목(취업, 연금 가입, 금융자산)만 현실적인 범위에서 바꿔 보며, 위험 상위 20% 경계 아래로 내려가는 가장 작은 변화를 찾는다. 나이·성별·학력·소득 이력은 바꾸지 않는다.</div>
{table(["패널", "위험 상위 20% 인원", "시도한 행동", "1개로 벗어남", "2개 이내로 벗어남", "모델이 말하는 취업 효과", "실제 관측(재취업자 − 미취업 유지자)"], [r7], 'style="font-size:7.4pt"')}
<h3>가장 흔한 최소 변화</h3>{table(["패널", "최소 변화 (위험 상위 20% 중 비율)"], [c7], num=[])}
<div class="box"><b class="t">방향 검증: {M7_["M7_verdict"]}</b>
t 시점 미취업자 {D7_["n"]:,}명을 모델 위험 10분위로 나눠 같은 위험끼리 비교하면, 2년 안에 재취업한 사람의 실제 지속 하락률이 계속 미취업인 사람보다 <b>{D7_["est"]*100:.1f}%p</b> 낮았다(95% {D7_["lo"]*100:.1f} ~ {D7_["hi"]*100:.1f}%p, 사람 단위 부트스트랩). 모델이 말하는 방향(취업 → 위험 감소)과 같다. 재정패널만 차이가 없었다({D7_["per"]["NaSTaB"]*100:+.1f}%p).</div>
<p><b>정직한 해석</b>: 위험 상위 20% 가운데 행동 1~2개로 경계를 벗어나는 사람은 <b>{pct(R7_.share_any.min(), 0)}~{pct(R7_.share_any.max(), 0)}</b>뿐이다. 위험의 대부분은 바꿀 수 없는 소득 이력(최근 4년 최저 소득, 변동성)에서 온다. 그래서 서비스의 “채우기 계획”은 개인 행동보다 <b>제도 연결(기초연금·주택연금·재취업지원)을 먼저</b> 제시하고, 반사실 결과는 “이런 변화가 있었던 사람들은 위험이 낮았다”는 예측으로만 표시한다(효과 보장 아님). 모델이 말하는 취업 효과(−0.4~−1.3%p)가 실제 관측 차이(−4.3%p)보다 작은 것도, 재취업 자체가 다른 좋은 조건과 함께 오기 때문으로 보이며, 인과로 말하지 않는 원칙과 맞다.</p>
</section>'''


DA = pickle.load(open(W + 'd123_out_D1.pkl', 'rb')); DB = pickle.load(open(W + 'd123_out_D2D3.pkl', 'rb'))
D1_, D2_, D3_ = DA['D1'], DB['D2'], DB['D3']
_d1p, _d1pl, _d1r = DA['D1_pool'], DA['D1_pool_placebo'], DA['D1_pool_red']
_pp = lambda x: f'{x*100:+.1f}%p'


def sec_ml3():
    r1 = ''.join(f'<tr><td>{NAME[r.panel]}</td><td class="n">{int(r.n):,}</td><td class="n">{pct(r.treated)}</td><td class="n">{_pp(r.raw)}</td><td class="n"><b>{_pp(r.ate)}</b> ± {r.se*196:.1f}</td><td class="n">{_pp(r.ate_red)}</td><td class="n">{_pp(r.placebo)} ± {r.se_placebo*196:.1f}</td><td class="n">{pct(r.overlap, 0)}</td></tr>' for _, r in D1_.iterrows())
    gap = DB['D2_gap']; mx = DB['D2_maxgap']
    r2 = ''.join(f'<tr><td>{NAME[p]}</td>' + ''.join(f'<td class="n">{gap.loc[(p, d), "지금 소득"]*100:.0f} → <b>{gap.loc[(p, d), "최종 모델"]*100:.0f}</b></td>' for d in ['성별', '학력', '나이', '가구', '취업']) + f'<td>{"통과" if mx.loc[p, "최종 모델"] <= mx.loc[p, "지금 소득"] + 0.02 else "미달"}</td></tr>' for p in ['KOWEPS', 'NaSTaB', 'KReIS', 'KLIPS'])
    piv = D2_[D2_.panel == 'KOWEPS'].pivot_table(index=['dim', 'group'], columns='model', values=['fnr', 'fpr'], sort=False)
    r2b = ''.join(f'<tr><td>{d}</td><td>{g}</td><td class="n">{pct(v[("fnr","지금 소득")], 0)} → <b>{pct(v[("fnr","최종 모델")], 0)}</b></td><td class="n">{pct(v[("fpr","지금 소득")], 0)} → {pct(v[("fpr","최종 모델")], 0)}</td></tr>' for (d, g), v in piv.iterrows())
    g3 = D3_.groupby('panel').agg(n=('year', 'size'), f=('auc_fixed', 'mean'), r=('auc_re', 'mean'), b=('auc_b0', 'mean'), gain=('gain', 'mean'), pos=('gain', lambda s: (s > 0).sum()))
    r3 = ''.join(f'<tr><td>{NAME[p]}</td><td class="n">{int(r.n)}</td><td class="n">{f3(r.b)}</td><td class="n">{f3(r.f)}</td><td class="n"><b>{f3(r.r)}</b></td><td class="n">{sgn(r.gain)}</td><td class="n">{int(r.pos)}/{int(r.n)}</td></tr>' for p, r in g3.iterrows())
    return f'''<section class="sec"><h2><span class="no">16-7</span>운영 수준 검증 – 인과 · 공정성 · 재학습 (D1·D2·D3)</h2>
<p>16-6까지는 “잘 맞히고 설명할 수 있나”였다. 여기서는 실제 운영에서 받을 세 질문을 실험했다. 판정 규칙은 실행 전에 <code>prereg_D123.txt</code>로 고정했다.</p>
<h3>16-7-1. D1 인과 ML – 재취업이 정말 위험을 낮추나 ({DA["D1_verdict"]})</h3>
<div class="def"><b>AIPW(이중 강건 추정)</b> – ML 모델 세 개를 쓴다. ① 누가 재취업하는지(성향 점수), ② 재취업한 사람의 결과, ③ 재취업하지 않은 사람의 결과. 두 모델을 섞어 효과를 추정하므로 둘 중 하나만 맞아도 편향이 없다. 모델은 LightGBM, 사람 단위 5겹 교차 적합(자기 데이터로 자기 효과를 추정하지 않음), 성향 0.02~0.98 밖은 제외.<br>
<b>위약 검증</b> – 미래의 재취업이 <b>과거</b>(t−2) 빈곤선 아래였는지에 “효과”를 내면 안 된다. 효과가 나오면 측정하지 못한 차이(교란)가 남아 있다는 뜻이다.</div>
{table(["패널", "t 미취업자", "2년 안 재취업", "단순 차이", "AIPW 효과 ± 95%", "이력 제외 AIPW", "위약 효과 ± 95%", "겹침 유지"], [r1], 'style="font-size:7.4pt"')}
<div class="box"><b class="t">판정: {DA["D1_verdict"]}</b>
4개 패널 결합 효과 <b>{_pp(_d1p[0])}</b> (95% {_pp(_d1p[1])} ~ {_pp(_d1p[2])}) → 상한 &lt; 0. 위약 효과 {_pp(_d1pl[0])} (95% {_pp(_d1pl[1])} ~ {_pp(_d1pl[2])}) → 0 포함. 두 조건 모두 통과.
즉 비슷한 조건(나이·소득 이력·가구·자산 등)의 미취업자 중 <b>2년 안에 재취업한 사람은 지속 하락 위험이 약 4%p 낮다</b>(기저 위험 15~23% 대비 약 5분의 1 감소). 16-6의 단순 관측 차이(−4.3%p)가 교란 보정 후에도 거의 유지됐다.</div>
<p><b>한계</b>: 측정한 변수로 설명되지 않는 차이(건강 악화 직후, 의욕 등)는 보정하지 못한다. 위약 점추정이 +1.9%p로 0 근처지만 상한이 +4.1%p라 완전히 배제하지는 못한다. 국민노후패널은 재취업자가 9%뿐이라 겹침이 44%만 유지되고 구간이 넓다. 그래서 서비스 문구는 “재취업은 위험을 약 4%p 낮추는 것으로 추정된다(관측 자료 기반)”까지이며, 확정적인 효과는 파일럿 무작위 배정으로 확인한다.</p>
<h3>16-7-2. D2 공정성 – 집단별로 놓치는 비율이 고르게 줄었나 ({DB["D2_verdict"]})</h3>
<div class="def"><b>미탐률</b> = 실제 지속 하락한 사람 중 위험 상위 20%에 들지 못한 비율. <b>오탐률</b> = 하락하지 않은 사람 중 상위 20%에 든 비율. 집단 간 미탐률 최대 격차를 지금 소득 기준과 비교했다(기준: 4개 중 3개 패널에서 최종 모델 격차 ≤ 지금 소득 격차 + 2%p).</div>
{table(["패널", "성별", "학력", "나이", "가구", "취업", "판정"], [r2])}
<p class="muted">칸 = 집단 간 미탐률 최대 격차(%p), 지금 소득 → 최종 모델.</p>
<h3>복지패널 집단별 미탐·오탐 (예시)</h3>{table(["축", "집단", "미탐률 (지금 소득 → 최종)", "오탐률 (지금 소득 → 최종)"], [r2b])}
<div class="box gray"><b class="t">판정: {DB["D2_verdict"]} (통과 {DB["D2_ok"]}/4)</b>
최종 모델은 <b>집단 {pct(DB["D2_share"], 0)}에서 미탐률이 같거나 낮아졌다</b>. 그런데 낮아지는 폭이 집단마다 달라서 격차가 커졌다. 1인 가구·고졸 미만·60대·미취업자의 미탐률은 크게 줄었고(예: 복지 1인 가구 24% → 6%), 50대·대졸 이상·취업자는 거의 그대로이거나 조금 늘었다. 모델이 “이력상 취약한 사람”에게 경보를 몰아 주는 셈이다. 그 결과 1인 가구 등에서는 오탐률도 올랐다.</div>
<p><b>정직한 해석</b>: 기준이 정한 “격차가 커지면 안 된다”는 통과하지 못했다. 다만 격차가 커진 방향은 <b>취약 집단을 더 놓치는 쪽이 아니라 상대적으로 유리한 집단(대졸·50대·취업자)의 하락을 덜 잡는 쪽</b>이다. 운영 원칙: ① 집단별 미탐·오탐표를 사이트 설명과 보고서에 공개, ② 50대 취업자처럼 “갑작스러운 하락”이 주인 집단을 위해 결과 화면에 “일이나 가구에 변화가 생기면 다시 진단하세요”를 안내. 집단별 경계값 조정은 따로 검증하지 않았으므로 적용하지 않는다.</p>
<h3>16-7-3. D3 운영 시뮬레이션 – 한 번 학습해 두면 되나, 매년 다시 학습해야 하나</h3>
<div class="def"><b>시뮬레이션</b> – 과거 시점에 서비스를 시작했다고 가정한다. ‘고정’은 가장 이른 자료(복지 2006, 노동 2005년 기준까지)로 한 번 학습하고 이후 계속 사용. ‘재학습’은 매년 그 시점까지 결과가 확정된 자료로 다시 학습. 매년 처음 보는 기준 연도로 채점했다.<br>
<b>PSI(분포 이동 지수)</b> – 중요 변수 10개가 학습 때와 비교해 얼마나 달라졌는지. 이것이 커질 때 성능이 떨어진다면 재학습 경보로 쓸 수 있다.</div>
<figure><img src="{img('g13_d3.png')}"><figcaption>그림 13. 기준 연도별 시험 AUC. 첫 해는 두 방식의 학습 자료가 같아 값이 같다.</figcaption></figure>
{table(["패널", "채점 연도 수", "지금 소득", "고정", "재학습", "재학습 − 고정", "재학습이 나은 해"], [r3])}
<div class="box"><b class="t">판정: {DB["D3_verdict_re"]} · PSI {DB["D3_verdict_alarm"]}</b>
재학습이 평균 <b>{sgn(DB["D3_gain"])}</b> 높았고, {len(D3_)}개 연도 중 {int((D3_.gain > 0).sum())}개에서 나았다(나머지는 정의상 같은 첫 해 2개와 복지 2021년 −0.000). 학습 자료가 쌓일수록 좋아지므로 <b>매년 재학습</b>이 운영 원칙이다. 고정 모델도 지금 소득보다는 평균 {sgn((D3_.auc_fixed - D3_.auc_b0).mean())} 높아, 재학습이 늦어져도 기준선 아래로 무너지지는 않았다.
반면 PSI와 성능 차이의 순위 상관은 {DB["D3_rho"]:.2f}(기준 0.5)로 <b>경보로 쓸 수 없었다</b>. 고정 모델의 첫 해 대비 하락으로 다시 재도 상관은 음수였다(−0.43). 성능 저하는 입력 분포 이동보다 학습 자료 양의 차이에서 왔다.</div>
<p>운영 설계에 반영: 재학습은 PSI 경보가 아니라 <b>매년 정기적으로</b> 하고, 새 차수의 결과가 확정될 때마다 직전 모델과 봉인 비교(새 모델이 낮으면 교체하지 않음)한다.</p>
</section>'''


def sec_maturity():
    return f'''<section class="sec"><h2><span class="no">16-9</span>머신러닝이 얼마나 업그레이드됐나</h2>
<p>처음 보고서(v1)에서 지금까지 ML이 보여주는 것이 어떻게 달라졌는지 다섯 단계로 정리했다.</p>
<table><tr><th style="width:17%">단계</th><th style="width:22%">무엇을 보여주나</th><th>처음 (v1)</th><th>지금</th></tr>
<tr><td><b>1. 예측력</b></td><td>기준보다 잘 맞히나</td><td>지금 소득 대비 +0.031</td><td>반복 관측 정답으로 <b>{sgn(mf["est"])}</b>, 복지 {f3(auc("KOWEPS_r", FIN))}. 일 전환 계산기형 대비 {sgn(t1["meta_calc"]["est"])}·{sgn(t2["meta_calc"]["est"])}</td></tr>
<tr><td><b>2. 검증의 엄격함</b></td><td>우연·누수·과적합이 아닌가</td><td>봉인 시험, 메타분석, 셔플, 학습곡선</td><td>+ 사람 단위 부트스트랩, 처음 보는 사람(+0.065), 집단 11개, 롤링 3시점(E1b), 이식·재보정</td></tr>
<tr><td><b>3. 모델 선택의 근거</b></td><td>언제 비선형 학습이 필요한가</td><td>사전 지정 HGB가 로지스틱보다 낮음</td><td>소득 하락: 차이 없음(근거와 함께). <b>일 전환: LightGBM이 로지스틱보다 유의하게 높음</b> ({sgn(t1["meta_lr"]["est"])})</td></tr>
<tr><td><b>4. 신뢰할 수 있는 출력</b></td><td>왜 그런 판단인가, 모르면?</td><td>전체 중요도·부분의존, 확률 어긋남</td><td><b>개인별 이유</b>(충실도 {MAa.ratio.min():.1f}~{MAa.ratio.max():.1f}배), <b>닮은 30명 사례</b>(3/4 통과), <b>판단 보류</b>(“안전” 중 하락 {pct(MAc.fall_in_safe.min())}~{pct(MAc.fall_in_safe.max())})</td></tr>
<tr><td><b>3-2. 표준 프로세스 점검</b></td><td>표준 기법을 다 써 봤나</td><td>튜닝 4조합, 불균형·결측·결합 방식 비교 없음</td><td>7단계 지도(0-2) + <b>P1~P6</b>: 튜닝 60회·불균형·스태킹·결측 대체 모두 v3와 차이 없음(천장 확인) · <b>PR-AUC·의사결정 곡선 5/5</b> · 1명 진단 {_P6["ms_one_shap"]:.1f}ms</td></tr>
<tr><td><b>4-2. 운영 신뢰성</b></td><td>인과·공정성·시간</td><td>없음</td><td><b>재취업 효과 AIPW {_pp(_d1p[0])}</b>(위약 통과) · 집단별 미탐률 격차 확대(공정성 기준 미달, 방향 공개) · <b>매년 재학습 {sgn(DB["D3_gain"])}</b>(PSI 경보는 무효)</td></tr>
<tr><td><b>5. 의사결정 지원</b></td><td>무엇을 물을지, 무엇을 바꿀지</td><td>없음</td><td>질문 수 고정(ML 선택 &gt; 전문가) 성공 · 적응형 질문 실패 · <b>가장 작은 변화</b> 방향 일치 확인(바꿀 수 있는 사람은 소수라는 것도 확인) · 사각지대는 같은 모델로 충분</td></tr></table>
<div class="box"><b class="t">한 줄 요약</b>처음에는 “계산보다 AUC가 조금 높은 예측기”였다. 지금은 <b>사람별로 이유를 말하고(숫자·사례), 모르면 판단을 보류하고, 무엇을 바꾸면 되는지와 그 한계까지 말하는 검증된 모델</b>이다. 여기에 재취업 효과를 인과 ML로 추정했고(위약 통과), 집단별 오탐·미탐표와 재학습 주기를 실험으로 정했다. 남은 과제는 집단 간 미탐 격차를 줄이는 방법과 파일럿 무작위 배정으로 효과를 확인하는 일이다.</div>
</section>'''


# ================= ML 프로세스 지도 + P1~P6 =================
PP = {}
for _f in ['P5P6', 'P2', 'P4', 'P3', 'P1']:
    PP.update(pickle.load(open(W + f'p16_out_{_f}.pkl', 'rb')))
_P6 = PP['P6']; TASKS_P = ['KOWEPS_r', 'NaSTaB_r', 'KReIS_r', 'KReIS_rn', 'KLIPS_r']
_m3 = lambda m: f'{sgn(m["est"])} [{sgn(m["lo"])}, {sgn(m["hi"])}]'
_chip = {'done': '<span class="pchip d">완료</span>', 'plus': '<span class="pchip p">이번 보강</span>', 'not': '<span class="pchip n">미실시</span>'}
_NMT = {'KOWEPS_r': '복지', 'NaSTaB_r': '재정', 'KReIS_r': '국민노후(빈곤선)', 'KReIS_rn': '국민노후(필요 생활비)', 'KLIPS_r': '노동'}


def sec_process():
    steps = [
        ('1', '요구사항 명확화', '무엇을, 어떤 조건에서, 얼마나 잘?',
         [('done', '목표: 50~69세 중 “지금은 괜찮은데 2년 안에 반복 부족해질 사람” 조기경보', '13'),
          ('done', '데이터: 국가 패널 6개 · 약관상 원자료 비공유 · 학습 {:,}행'.format(n_tr_all), '1'),
          ('done', '최소 성능: 지금 소득보다 AUC +0.03, 결합 하한 &gt; 0 (사전 등록)', '4·5'),
          ('plus', f'시스템 요구: 1명 진단 {_P6["ms_one_shap"]:.1f}ms · 10만 명 {_P6["s_batch"]:.1f}초 실측 (P6)', '16-8')]),
        ('2', 'ML 문제로 구조화', 'ML이 정말 필요한가?',
         [('done', '규칙 기반(지금 소득·계산기형·충족률)과 정면 비교 → ML이 모두 이김', '5·6·15'),
          ('done', 'ML 목표: 지속 하락 이진 분류, AUC + 같은 인원 발견 수', '3'),
          ('done', '입력 공통 17개 + 패널별 추가 → 출력 위험 순위·이유 3개·판단 보류', '13-1')]),
        ('3', '데이터 준비', '수집 → 정제 → 변환 → 축소 → 분할',
         [('done', '6개 패널 공통 스키마(ETL), CPI 실질화, 균등화, 가처분소득', '1·2'),
          ('done', '정제: 극단값 0.5% 절단 · 피처: 최저 소득·변동성·변화량 등 이력 변수', '2'),
          ('plus', f'결측 처리 3가지 비교 → {PP["P4_verdict"]} (P4)', '16-8'),
          ('done', '축소: 질문 12개 고정 시 ML 선택 &gt; 전문가 양식', '8')]),
        ('4', '모델 개발', '기준선 → 단순 → 복잡 → 앙상블',
         [('done', '기준선 2종 → 15종 비교 → LightGBM+로지스틱 앙상블', '6'),
          ('done', '분할: 시간 봉인 시험 + 사람 단위 교차검증(같은 사람 섞임 방지)', '4'),
          ('plus', f'하이퍼파라미터 60회 베이지안 탐색 → {PP["P1_verdict"]} (P1)', '16-8'),
          ('plus', f'클래스 불균형 처리 → {PP["P2_verdict"]} (P2) · 스태킹 → {PP["P3_verdict"]} (P3)', '16-8')]),
        ('5', '평가', '오프라인 → 온라인',
         [('done', 'DeLong·메타분석·사람 단위 부트스트랩·학습곡선·라벨 셔플', '5·7·9'),
          ('done', '집단별·처음 보는 사람·보정·이식 · 공정성(D2)', '11·12·16-7'),
          ('plus', f'불균형용 지표 PR-AUC·정밀도·의사결정 곡선 → PR-AUC {PP["P5_A"]}, 순이득 {PP["P5_B"]} (P5)', '16-8'),
          ('not', '온라인 A/B 평가 → 파일럿에서 무작위 배정으로', '13')]),
        ('6', '배포', '어디서, 어떻게 예측하나',
         [('done', '미리사주 웹(GitHub Pages) + 진단·챗봇 서버(Render), 입력 비저장', '13-1'),
          ('plus', f'모델 {_P6["kb"]:.0f}KB, 압축 불필요 · 실시간 진단 + 야간 배치 모두 가능 (P6)', '16-8'),
          ('done', '출력 신뢰: 개인별 이유(M-A) · 판단 보류(M-C) · 닮은 30명(M3)', '16')]),
        ('7', '모니터링', '세상이 바뀌면?',
         [('done', '데이터 드리프트: PSI 측정 → 경보로는 무효(정직하게 공개)', '16-7'),
          ('done', '컨셉 드리프트: 매년 재학습 +0.022, 새 모델이 낮으면 교체 안 함', '16-7')]),
    ]
    rows = ''
    for no, name, q, items in steps:
        li = ''.join(f'<div class="pit">{_chip[s]}<span class="ptx">{t}</span><span class="psec">{sec}</span></div>' for s, t, sec in items)
        rows += f'<div class="pst"><div class="pno">{no}</div><div class="phd"><b>{name}</b><span>{q}</span></div><div class="pbody">{li}</div></div>'
    return f'''<section class="sec"><h2><span class="no">0-2</span>ML 프로세스 지도 – 표준 7단계로 본 이 프로젝트</h2>
<p>머신러닝 프로젝트의 표준 7단계(요구사항 → 문제 구조화 → 데이터 → 모델 → 평가 → 배포 → 모니터링)에 이 보고서를 대응시켰다. 오른쪽 숫자는 자세한 장이다. <b>이번 보강</b>은 이 점검에서 빈칸으로 찾은 항목을 실험으로 채운 것(P1~P6, 16-8)이다.</p>
<style>
.pst {{ display:grid; grid-template-columns: 9mm 38mm 1fr; gap: 2.5mm; padding: 2.2mm 0; border-bottom: .6px solid var(--rule); break-inside: avoid; }}
.pno {{ width:8mm; height:8mm; border-radius:50%; background:var(--blue); color:#fff; font-weight:700; display:flex; align-items:center; justify-content:center; font-size:10pt; }}
.phd b {{ display:block; font-size:9.6pt; }} .phd span {{ font-size:7.8pt; color:var(--ink2); }}
.pit {{ display:grid; grid-template-columns: 15mm 1fr 12mm; gap:2mm; font-size:8.1pt; margin-bottom:1mm; align-items:baseline; }}
.psec {{ text-align:right; color:var(--ink3); font-size:7.6pt; }}
.pchip {{ font-size:6.8pt; padding:.2mm 1.4mm; border-radius:1.5mm; text-align:center; white-space:nowrap; }}
.pchip.d {{ background:var(--soft); color:var(--ink2); }} .pchip.p {{ background:var(--blue-bg); color:var(--blue); font-weight:700; }} .pchip.n {{ background:#fdeee7; color:var(--orange); font-weight:700; }}
</style>
{rows}
<div class="box" style="margin-top:4mm"><b class="t">점검 결과</b>표준 7단계 중 빈칸은 4단계(모델 개발)에 몰려 있었다: 하이퍼파라미터 탐색이 모델당 4조합뿐, 클래스 불균형·스태킹·결측 처리는 비교 없이 기본값을 썼다. 여기에 불균형용 평가 지표와 배포 실측까지 6개를 사전 등록 실험으로 채웠다. 남은 빈칸은 온라인 평가(A/B) 하나이며, 이는 실제 서비스 파일럿에서만 가능하다.</div>
</section>'''


def sec_p16():
    P5 = PP['P5']; pv = lambda k, m, c: P5[(P5.task == k) & (P5.model == m)][c].iloc[0]
    r5 = ''.join(f'<tr><td>{_NMT[k]}</td><td class="n">{pct(pv(k, "지금 소득", "base"))}</td><td class="n">{f3(pv(k, "지금 소득", "prauc"))}</td><td class="n">{f3(pv(k, "계산기형", "prauc"))}</td><td class="n"><b>{f3(pv(k, "최종 모델", "prauc"))}</b></td><td class="n">{pct(pv(k, "지금 소득", "prec20"))} → <b>{pct(pv(k, "최종 모델", "prec20"))}</b></td><td class="n">{pv(k, "지금 소득", "lift20"):.1f} → <b>{pv(k, "최종 모델", "lift20"):.1f}</b>배</td></tr>' for k in TASKS_P)
    B5 = PP['P5_boot']; win = PP['P5_win']
    b5 = ' · '.join(f'{_NMT[r.task]} {sgn(r.d)} [{sgn(r.lo)}, {sgn(r.hi)}]' for _, r in B5.iterrows())
    w5 = ''.join(f'<tr><td>{_NMT[k]}</td><td class="n">{win.loc[k, "all"]*100:+.2f}</td><td class="n">{win.loc[k, "계산기형"]*100:+.2f}</td><td class="n"><b>{win.loc[k, "LightGBM"]*100:+.2f}</b></td></tr>' for k in TASKS_P)
    P2 = PP['P2']
    r2 = ''.join(f'<tr><td>{_NMT[k]}</td>' + ''.join(f'<td class="n">{f3(g[g.method == m].auc.iloc[0])}</td>' for m in ['v3 (처리 없음)', '가중치(scale_pos_weight)', '언더샘플링 1:1']) + ''.join(f'<td class="n">{pct(g[g.method == m].ece.iloc[0])}</td>' for m in ['v3 (처리 없음)', '가중치(scale_pos_weight)', '언더샘플링 1:1']) + f'<td class="n">{pct(g.obs.iloc[0])}</td></tr>' for k, g in P2.groupby('task', sort=False))
    P4 = PP['P4']; inf = P4[P4.method == '_info'].set_index('task')
    r4 = ''.join(f'<tr><td>{_NMT[k]}</td><td class="n">{int(inf.loc[k, "miss_cols"])}</td><td class="n">{pct(inf.loc[k, "miss_rows"], 0)}</td>' + ''.join(f'<td class="n">{f3(g[g.method == m].auc.iloc[0])}</td>' for m in ['LightGBM 기본 처리 (v3)', '중앙값 + 결측 표시', '반복 대체 + 결측 표시']) + '</tr>' for k, g in P4[P4.method != '_info'].groupby('task', sort=False))
    P3 = PP['P3']; C3 = PP['P3_coef'].set_index('task')
    r3 = ''.join(f'<tr><td>{_NMT[r.task]}</td><td class="n">{f3(r.auc_lgb)}</td><td class="n">{f3(r.auc_final)}</td><td class="n"><b>{f3(r.auc_stack)}</b></td><td class="n">{sgn(r.auc_stack - r.auc_final)}</td><td style="font-size:7.4pt">' + ' · '.join(f'{n} {C3.loc[r.task, n]:.2f}' for n in ['LightGBM', 'XGBoost', 'CatBoost', 'LR_L2']) + '</td></tr>' for _, r in P3.iterrows())
    P1 = PP['P1']; B1 = PP['P1_best'].set_index('task')
    r1 = ''.join(f'<tr><td>{_NMT[r.task]}</td><td class="n">{f3(r.inner_old)} → {f3(r.inner_new)}</td><td class="n">{f3(r.auc_old)}</td><td class="n"><b>{f3(r.auc_new)}</b></td><td class="n">{sgn(r.auc_new - r.auc_old)}</td><td class="n">{f3(r.auc_fin_old)} → {f3(r.auc_fin_new)}</td><td style="font-size:7.2pt">잎 {B1.loc[r.task, "num_leaves"]} · 최소 표본 {B1.loc[r.task, "min_child_samples"]} · 학습률 {B1.loc[r.task, "learning_rate"]:.3f}</td></tr>' for _, r in P1.iterrows())
    return f'''<section class="sec"><h2><span class="no">16-8</span>ML 프로세스 점검 실험 (P1~P6)</h2>
<p>0-2의 7단계 점검에서 빈칸으로 찾은 6개 항목을 실험으로 채웠다. 판정 규칙은 실행 전에 <code>prereg_P16.txt</code>로 고정했다. 판정용 차이는 v3와 같은 방식(과제별 DeLong → 판정 3개 과제 랜덤효과 메타)이다.</p>
<table><tr><th style="width:6%"></th><th style="width:22%">실험</th><th style="width:12%">단계</th><th>판정 기준</th><th style="width:22%">결과</th></tr>
<tr><td>P1</td><td>하이퍼파라미터 탐색 확장</td><td>4 모델 개발</td><td>튜닝 − v3 메타 하한 &gt; 0</td><td>{_m3(PP["P1_meta"])} → <b>{PP["P1_verdict"]}</b></td></tr>
<tr><td>P2</td><td>클래스 불균형 처리</td><td>4 모델 개발</td><td>어느 방식이든 − v3 메타 하한 &gt; 0</td><td>가중치 {_m3(PP["P2_spw_meta"])} · 언더 {_m3(PP["P2_un_meta"])} → <b>{PP["P2_verdict"]}</b></td></tr>
<tr><td>P3</td><td>스태킹</td><td>4 모델 개발</td><td>스태킹 − v3 최종 메타 하한 &gt; 0</td><td>{_m3(PP["P3_meta"])} → <b>{PP["P3_verdict"]}</b></td></tr>
<tr><td>P4</td><td>결측 처리 비교</td><td>3 데이터 준비</td><td>대안 − v3 메타 하한 &gt; 0이면 교체</td><td>중앙값 {_m3(PP["P4_med_meta"])} · 반복 {_m3(PP["P4_it_meta"])} → <b>{PP["P4_verdict"]}</b></td></tr>
<tr><td>P5</td><td>불균형용 평가 지표</td><td>5 평가</td><td>PR-AUC 5/5 + 하한 &gt; 0 · 순이득 4/5</td><td>PR-AUC <b class="ok">{PP["P5_A"]}</b> · 순이득 <b class="ok">{PP["P5_B"]} {PP["P5_Bok"]}/5</b></td></tr>
<tr><td>P6</td><td>배포 실측</td><td>6 배포</td><td>1명+이유 &lt; 50ms, 10만 명 &lt; 60초</td><td><b class="ok">{PP["P6_verdict"]}</b></td></tr></table>

<h3>P1. 하이퍼파라미터 탐색 확장 – “덜 튜닝해서 0.80에 멈춘 것 아닌가”</h3>
<div class="def"><b>하이퍼파라미터</b> – 학습 전에 사람이 정하는 설정(트리 잎 수, 학습률, 규제 강도 등). <b>베이지안 탐색(Optuna TPE)</b> – 앞서 시도한 조합의 결과를 보고 좋아 보이는 영역을 골라 다음 조합을 고르는 탐색. 무작위보다 적은 횟수로 좋은 설정을 찾는다.<br>
v3는 LightGBM에서 잎 수 2개 × 최소 표본 2개 = 4조합만 봤다. 이번에는 8개 설정을 동시에 60회 탐색했다. 탐색은 학습 앞부분 → 내부 검증으로만 하고 시험셋은 보지 않았다.</div>
{table(["과제", "내부 검증 AUC (v3 → 탐색)", "시험 v3", "시험 탐색", "차이", "최종 앙상블 (v3 → 탐색)", "찾은 설정"], [r1], 'style="font-size:7.4pt"')}
<p><b>해석</b>: 탐색은 5개 과제 모두에서 내부 검증 점수를 올렸다(+0.003~+0.023). 그러나 처음 보는 시험 연도에서는 큰 패널(복지·재정)만 +0.002 정도 올랐고, 표본이 작은 국민노후패널은 내부 검증 +0.023이 시험에서 <b>−0.018로 뒤집혔다</b>. 60번 시도하면서 작은 검증셋의 우연한 패턴에 맞춘 것(검증셋 과적합)이다. 결합하면 {_m3(PP["P1_meta"])}로 0을 포함한다. 즉 성능 천장은 <b>튜닝 부족이 아니라 입력 정보의 한계</b>다. 6장에서 15종 모델이 같은 높이에서 멈춘 것과 같은 결론이다. 작은 탐색 공간(4조합)이 오히려 작은 패널에서 안전했다는 점도 확인됐다. v3 설정을 유지한다.</p>

<h3>P2. 클래스 불균형 처리 – 하락자가 6~10%뿐인데 그대로 학습해도 되나</h3>
<div class="def"><b>클래스 불균형</b> – 한쪽 정답(지속 하락자)이 훨씬 적은 상태. <b>가중치</b>는 하락자 한 명을 틀릴 때 벌점을 키우고, <b>언더샘플링</b>은 비하락자를 하락자 수만큼만 뽑아 1:1로 학습한다. <b>ECE</b>는 예측 확률과 실제 비율의 평균 어긋남(낮을수록 좋음).</div>
{table(["과제", "AUC v3", "AUC 가중치", "AUC 언더", "ECE v3", "ECE 가중치", "ECE 언더", "실제 하락률"], [r2], 'style="font-size:7.6pt"')}
<p><b>해석</b>: 순위(AUC·상위 20% 재현율)는 거의 같고, 확률은 크게 부풀었다(예: 복지 실제 6.0%인데 평균 예측 26~28%). 우리 서비스는 순위로 경보하므로 불균형 처리의 이득이 없고, 확률 표시는 망가진다 → <b>{PP["P2_verdict"]}</b>. 트리 부스팅은 불균형 자체에 강하고, 불균형 문제는 지표(P5)로 다루는 것이 맞다.</p>

<h3>P3. 스태킹 – 앙상블을 사람이 정하지 말고 학습시키면</h3>
<div class="def"><b>스태킹</b> – 여러 모델의 예측을 입력으로 받는 ‘상위 모델’을 학습하는 앙상블. 상위 모델은 학습셋의 교차검증 예측(사람 단위 5겹)으로만 학습해 자기 답을 외우지 않게 했다. 비교 대상 v3 최종은 LightGBM과 로지스틱의 순위 평균(가중치 1:1 고정)이다.</div>
{table(["과제", "LightGBM", "v3 최종 (순위 평균)", "스태킹", "스태킹 − v3", "상위 모델 가중치(로짓)"], [r3], 'style="font-size:7.6pt"')}
<p><b>해석</b>: {_m3(PP["P3_meta"])} → <b>{PP["P3_verdict"]}</b>. 오히려 5개 과제 모두에서 순위 평균보다 약간 낮았다(−0.001~−0.006). 상위 모델 가중치를 보면 XGBoost·CatBoost가 과제마다 음수와 양수를 오간다. 네 모델의 예측이 서로 거의 같아서(같은 신호를 잡음) 상위 모델이 미세한 차이에 과적합한 것이다. 결합 방식을 학습해도 더 얻을 것이 없으므로, 단순하고 설명하기 쉬운 순위 평균을 유지한다.</p>

<h3>P4. 결측 처리 – 패널 탈락·무응답을 어떻게 다룰까</h3>
<div class="def"><b>결측</b> – 값이 비어 있는 칸(조사 중간 탈락, 과거 이력 없음, 무응답). v3는 LightGBM이 결측을 따로 한쪽 가지로 보내는 <b>기본 처리</b>를 썼다. 대안 ① <b>중앙값 대체 + 결측 표시</b>(빈칸을 중앙값으로 채우고 “비어 있었음” 변수 추가), ② <b>반복 대체</b>(다른 변수로 빈칸을 예측해 채우기를 5회 반복 + 결측 표시).</div>
{table(["과제", "결측 있는 입력 수", "결측 있는 행", "기본 처리 (v3)", "중앙값 + 표시", "반복 대체 + 표시"], [r4])}
<p><b>해석</b>: 결측이 있는 행이 많지만(이력 변수는 처음 조사된 사람에게 비어 있음), 세 방식의 차이는 작다 → <b>{PP["P4_verdict"]}</b>. 결측 자체가 “조사 이력이 짧다”는 정보이므로 그대로 두는 기본 처리가 정보를 버리지 않는다.</p>

<h3>P5. 불균형용 평가 지표 – AUC만 보면 가려지는 것</h3>
<div class="def"><b>PR-AUC(평균 정밀도)</b> – “경보를 울린 사람 중 실제 하락자 비율(정밀도)”을 재현율 전 구간에서 평균. 하락자가 드물수록 AUC보다 엄격하다. 무작위 모델의 PR-AUC = 하락률.<br>
<b>리프트</b> – 상위 20%의 하락률 ÷ 전체 하락률. <b>의사결정 곡선</b> – 경보 기준 확률 p에서 순이득 = (맞힌 하락자 − 헛경보 × p/(1−p)) ÷ 전체. “전원 경보”나 “무경보(0)”보다 높아야 쓸 가치가 있다.</div>
{table(["과제", "하락률", "PR-AUC 지금 소득", "PR-AUC 계산기형", "PR-AUC 최종", "상위 20% 정밀도", "리프트"], [r5], 'style="font-size:7.6pt"')}
<p>최종 − 지금 소득 PR-AUC(사람 단위 부트스트랩 95%): {b5} → 모두 하한 &gt; 0, <b class="ok">{PP["P5_A"]}</b>.</p>
<figure><img src="{img('g14_dca.png')}"><figcaption>그림 14. 의사결정 곡선. 파란 음영 = 판정 구간(기준 확률 0.10~0.30). 회색 점선 = 전원 경보, 검은 선 = 무경보.</figcaption></figure>
{table(["과제", "전원 경보", "계산기형", "ML (LightGBM)"], [w5])}
<p class="muted">기준 확률 0.10~0.30 평균 순이득(100명당 명). 예: +2.15 = 100명을 진단하면 헛경보 비용을 빼고도 하락자 약 2명을 순수하게 잡는다. 전원 경보는 헛경보가 너무 많아 음수다.</p>
<p><b>해석</b>: 하락자가 6~10%뿐이라 PR-AUC 절대값은 0.25~0.33이지만, 무작위(=하락률)보다 2.5~5.5배, 지금 소득보다 {sgn(B5.d.min())}~{sgn(B5.d.max())} 높다. 상위 20%에 경보하면 하락자를 무작위보다 {P5[P5.model == "최종 모델"].lift20.min():.1f}~{P5[P5.model == "최종 모델"].lift20.max():.1f}배 많이 담는다. 의사결정 곡선에서는 <b>5개 과제 모두 ML이 계산기형·전원 경보보다 순이득이 높았다</b>. 즉 상담 자원이 한정된 기관이 어떤 기준을 쓰든 ML 순위를 쓰는 편이 이득이다.</p>

<h3>P6. 배포 실측 – 실시간 서비스가 되나</h3>
<table><tr><th>항목</th><th class="n">측정값</th><th>의미</th></tr>
<tr><td>1명 예측 (중앙값 / 95%)</td><td class="n">{_P6["ms_one"]:.1f} / {_P6["ms_one_p95"]:.1f} ms</td><td>개인 진단 화면에서 즉시 응답</td></tr>
<tr><td>1명 예측 + 개인별 이유(TreeSHAP)</td><td class="n">{_P6["ms_one_shap"]:.1f} / {_P6["ms_one_shap_p95"]:.1f} ms</td><td>기준 50ms의 {_P6["ms_one_shap"]/50*100:.0f}%</td></tr>
<tr><td>10만 명 배치 예측</td><td class="n">{_P6["s_batch"]:.1f} 초</td><td>동시 이용이 몰려도 여유</td></tr>
<tr><td>10만 명 배치 + 개인별 이유</td><td class="n">{_P6["s_batch_shap"]:.1f} 초</td><td>상담 화면용 이유 3개 사전 계산</td></tr>
<tr><td>모델 크기</td><td class="n">{_P6["kb"]:.0f} KB ({_P6["trees"]}개 트리, 입력 {_P6["n_feat"]}개)</td><td>지식 증류·양자화 같은 압축 불필요, 기관 내부(온프레미스) 설치도 가능</td></tr></table>
<p class="muted">2 CPU 클라우드 환경, 복지패널 모델 기준. 판정: <b>{PP["P6_verdict"]}</b>. 그래서 미리사주는 요청마다 실시간으로 계산한다.</p>

<div class="box"><b class="t">P1~P6이 말해 주는 것</b>모델 개발 단계의 표준 기법(튜닝 확장 · 불균형 처리 · 스태킹 · 결측 대체)은 <b>모두 v3보다 유의하게 낫지 않았다</b>. 이것은 실패가 아니라, v3가 이미 이 데이터가 줄 수 있는 성능에 도달했다는 네 가지 독립된 증거다. 대신 평가(P5)와 배포(P6)에서는 서비스 가치가 숫자로 확인됐다: 불균형에 엄격한 지표로도 ML이 이기고, 실시간 진단이 가능하다.</div>
</section>'''


# ================= 미리사주 서비스 모델 =================
SO = pickle.load(open(W + 's_out.pkl', 'rb')); SPC = pickle.load(open(W + 's_pathcheck.pkl', 'rb'))


def sec_service():
    rr = [SO[('KOWEPS', 'S20')]['res'], SO[('KOWEPS', 'S21')]['res'], SO[('NaSTaB', 'S20')]['res']]
    nm = ['복지 · 건강 제외 (기본)', '복지 · 건강 포함', '재정 · 건강 제외 (재현)']
    r1 = ''.join(f'<tr><td>{n}</td><td class="n">{r["n_feat"]}</td><td class="n">{f3(r["auc_full"])}</td><td class="n"><b>{f3(r["auc_service"])}</b></td><td class="n">{r["loss"]:+.4f} [{r["loss_lo"]:+.4f}, {r["loss_hi"]:+.4f}]</td><td class="n">{f3(r["auc_b0"])}</td><td class="n">{sgn(r["vs_b0"])} (하한 {sgn(r["vs_b0_lo"])})</td><td class="n">{pct(r["cov_pos"])} / {pct(r["cov_neg"])}</td><td>{"<span class=ok>통과</span>" if (r["pass1"] and r["pass2"]) else "<span class=no>미달</span>"}{"" if i < 2 else " (보고만)"}</td></tr>' for i, (n, r) in enumerate(zip(nm, rr)))
    S = SO['sens']
    r2 = ''.join(f'<tr><td>{c.cond}</td><td class="n">{f3(c.auc)}</td><td class="n">{-c["drop"]:+.4f}</td></tr>' for _, c in S.iterrows())
    return f'''<section class="sec"><h2><span class="no">16-10</span>미리사주 서비스 모델 – 화면 21문항만으로도 맞히나</h2>
<p>서비스 이름을 <b>미리사주</b>로 바꾸면서 화면 입력을 21문항으로 정했다. 보고서의 모델(입력 43개)에는 사용자가 답할 수 없는 변수(세전 소득, 직업·지역 코드, 4년 전 소득 등)가 있어, 화면 문항만으로 다시 학습하고 같은 시험으로 손실을 쟀다. 판정 기준은 실행 전에 <code>prereg_S.txt</code>로 고정했다.</p>
<div class="def"><b>화면 21문항</b> – 출생연도, 성별, 배우자, 학력, 가구원 수(지금·2년 전), 공적연금 수령, 퇴직연금·개인연금 가입, 가구 월 실수령 소득(지금·1년 전·2년 전), 일함(지금·1년 전·2년 전), 일의 형태, 자가, 금융자산, 부동산, 부채, 건강(선택).<br>
<b>보고서와 같게 유지한 것</b> – 정답 v3, 같은 학습·봉인 시험 행, LightGBM 내부 검증 튜닝 + 로지스틱, 순위 결합, 사람 단위 부트스트랩.<br>
<b>이번에 고친 것</b> – ① 복지패널 부동산에 사는 집 가격(h06_6, 자가일 때) 포함(코드북·원자료로 확인), ② 가구원 변화는 정수 차(사별 −, 귀가 +), ③ 금액은 2025년 물가, ④ 소득 이력은 지금·1년 전·2년 전(복지·재정은 매년 조사라 그대로 존재).</div>
<h3>판정: 전체 입력 모델 대비 손실</h3>
<p class="muted">기준 1: 손실 점추정 ≤ 0.01 이고 95% 상한 ≤ 0.02 (주 판정 = 복지 · 건강 제외). 기준 2: 지금 소득만 대비 DeLong 하한 &gt; 0. 국민노후패널은 격년 조사라 "1년 전 소득"이 없어 제외했다.</p>
{table(["모델", "입력 수", "전체 모델 AUC", "서비스 AUC", "손실 [95%]", "지금 소득만", "지금 소득 대비", "판단 보류 포함률(하락/비하락)", "판정"], [r1], 'style="font-size:7.2pt"')}
<div class="box"><b class="t">결과: 통과</b>
화면 문항만 쓴 모델의 손실은 {rr[0]["loss"]:+.4f}(상한 {rr[0]["loss_hi"]:+.4f})로 사실상 0이다. 건강을 넣어도 {rr[1]["loss"]:+.4f}로 차이가 없어, <b>민감 정보인 건강은 묻지 않는 것을 기본으로 한다</b>. 지금 소득만 볼 때보다는 여전히 {sgn(rr[0]["vs_b0"])} 높다. 이유: 보고서 모델의 상위 변수(지금 소득, 가구원 수, 최저 소득, 1년 사이 변화, 나이·연금 개시 거리, 배우자)를 화면이 모두 묻고, 빠진 변수(직업·지역 코드, 2년 전 건강 등)는 중요도가 낮았다. 서비스 위험 상위 20%의 실제 하락률은 22.0%(전체 6.0%의 약 3.7배)다.</div>
<h3>회상 소득 민감도 (화면 경로의 약점 점검)</h3>
<p>패널 소득은 조사 기록이고 화면의 1년 전·2년 전 소득은 기억이다. 모델은 그대로 두고 시험셋의 과거 소득에만 오차를 넣었다(잡음은 20회 평균).</p>
{table(["가정한 오차", "AUC", "변화"], [r2])}
<p>±20% 잡음에서 {-S["drop"].iloc[0]:+.4f}로 허용 기준(0.01) 안이다. 과거 소득을 낮게 기억하는 치우침은 오히려 AUC를 조금 올렸는데, 낮춰 말한 사람을 모델이 더 위험하게 보는 방향이 실제 하락과 겹치기 때문으로 보인다. 단, 실제 회상 오차의 크기는 패널로 잴 수 없으므로 <b>가정한 오차 범위의 민감도</b>로만 말한다.</p>
<h3>화면 → 모델 경로 검증</h3>
<p>시험 4,984명의 기록을 화면 입력 형태(월 소득, 출생연도, 일의 형태 등)로 되돌려 배포용 <code>predict.py</code>에 넣었다. 학습 때 점수와 상관 {SPC["corr"]:.4f}, AUC {SPC["auc_train"]:.4f} → {SPC["auc_api"]:.4f}. 남은 차이는 화면이 "1년 전 가구원 수"를 묻지 않아 지금 가구원 수로 근사한 데서 온다.</p>
<p class="muted">한계: 서비스 모델은 복지패널로 학습했다(재정패널은 재현만). 2025년 이후 빈곤선은 2024년 값과 실질 같다고 가정했다. 공개·영리 서비스 사용은 패널 기관 확인 전이다.</p>
</section>'''
