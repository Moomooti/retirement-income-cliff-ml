"""피드백 반영: ① 빈곤·상위·줄세우기 표현 순화 ② 결과 맨 위 한 줄 풀이 + 근거는 접기 ③ 빚 종류·상환 어려움에 따라 안내 ④ 화면 빈곤선 상수 = 모델 기준"""
import sys, re
src, out = sys.argv[1:3]
s = open(src, encoding='utf-8').read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)

# ---------- ④ 기준선 상수: 모델(constants.json)과 같은 값 ----------
rep("const LINE_YEAR = 1859;   // 1인 기준 연 가처분 빈곤선(만원, 2025년 물가)",
    "const LINE_YEAR = 1882;   // 1인 기준 연 생활 기준선(가처분 중위소득의 50%, 만원, 2025년 물가) – 모델 constants.json과 같은 값")

# ---------- CSS ----------
rep('</style>\n</head>', '''
/* 결과 한 줄 풀이 · 근거 접기 */
.sum{margin:14px 0 4px;padding:14px 16px;border-radius:14px;background:rgba(212,166,55,.10);border:1px solid rgba(212,166,55,.35)}
.sum .head{margin:0;font-family:var(--batang);font-size:17px;line-height:1.65;color:var(--text)}
.sum ul{margin:10px 0 0;padding-left:18px;font-size:14px;color:var(--text2);line-height:1.7}
.sum ul b{color:var(--text)}
details.more{margin-top:18px;border-top:1px dashed var(--line2);padding-top:12px}
details.more>summary{cursor:pointer;font-weight:700;font-size:14px;color:var(--ember);list-style:none}
details.more>summary::-webkit-details-marker{display:none}
details.more>summary::before{content:"▸ ";}
details.more[open]>summary::before{content:"▾ ";}
.defn{font-size:12.5px;color:var(--text3);margin:6px 0 0}
</style>
</head>''')

# ---------- 빚: 선택 질문 (모델에는 보내지 않음) ----------
rep('''(한 달 상환액 아님). 없으면 0.</div>
      </div>''', '''(한 달 상환액 아님). 없으면 0.</div>
      </div>
      <div class="fld hidden" id="debtMore"><span class="lbl">빚에 대해 조금만 더 <span class="tag">선택</span></span>
        <div class="seg" data-k="debt_type"><button type="button" data-v="mortgage">주택담보·전세대출이 대부분</button><button type="button" data-v="other">신용대출·카드 등이 대부분</button><button type="button" data-v="mix">섞여 있음</button></div>
        <div class="seg" data-k="debt_stress" style="margin-top:8px"><button type="button" data-v="ok">잘 갚고 있어요</button><button type="button" data-v="tight">갚기 빠듯해요</button><button type="button" data-v="overdue">연체 중이거나 연체될 것 같아요</button></div>
        <div class="hint">풀이(모델)에는 쓰지 않고, 아래 '다음 걸음' 안내를 고르는 데만 써요. 답하지 않아도 돼요.</div></div>''')
rep("$('jobTypeFld').classList.add('hidden');",
    "$('jobTypeFld').classList.add('hidden');\n$('debt').addEventListener('input', () => $('debtMore').classList.toggle('hidden', !(num('debt') > 0)));")
rep("    health: sel.health ? Number(sel.health) : null,",
    "    health: sel.health ? Number(sel.health) : null,\n    debt_type: sel.debt_type, debt_stress: sel.debt_stress,               // 안내용(모델 입력 아님)")

# ---------- 이유 문장 ----------
rep("s_log_r: `지금 1인 기준 소득이 빈곤선의 약 ${r0.toFixed(2)}배예요.`,", "s_log_r: `지금 1인 기준 소득이 생활 기준선의 약 ${r0.toFixed(2)}배예요.`,")
rep("s_min3: `최근 3년 중 가장 낮았던 해의 소득이 빈곤선의 약 ${Math.min(r0, r1, r2).toFixed(2)}배였어요. 한 번 낮아졌던 기록은 다시 내려갈 가능성과 이어져요.`,",
    "s_min3: `최근 3년 중 가장 적었던 해의 소득이 생활 기준선의 약 ${Math.min(r0, r1, r2).toFixed(2)}배였어요. 한 번 출렁였던 소득은 다시 출렁이기 쉬워요.`,")
rep("female: `성별(${P.female ? '여성' : '남성'})에 따른 패널 속 평균적인 차이예요.`",
    "female: `비슷한 조건의 분들에게서 보인 통계적인 경향이에요(성별).`")
rep("edu3: `학력(${['고졸 미만', '고졸', '대졸 이상'][P.edu3]})에 따른 패널 속 평균적인 차이예요.`,",
    "edu3: `비슷한 조건의 분들에게서 보인 통계적인 경향이에요(학력).`,")
rep("s_debt_r: `남은 빚 ${fmt(P.debt)}만원, 연소득의 ${xr(P.debt)}배예요.`, s_lg_debt: `남은 빚이 ${fmt(P.debt)}만원이에요.`,",
    "s_debt_r: `남은 빚 ${fmt(P.debt)}만원, 연소득의 ${xr(P.debt)}배예요.${debtNote(P)}`, s_lg_debt: `남은 빚이 ${fmt(P.debt)}만원이에요.${debtNote(P)}`,")
rep("function reasonText(f, P, up){", """function debtNote(P){
  if (P.debt_stress === 'ok' || (P.debt_type === 'mortgage' && P.debt_stress !== 'tight' && P.debt_stress !== 'overdue')) return ' 주택담보대출처럼 계획대로 잘 갚고 있는 빚이라면 이 숫자만으로 걱정할 일은 아니에요.';
  return '';
}
// 서버 라벨 중 화면에 맞게 부드럽게 바꿀 것
const FLABEL = { s_log_r: '지금 소득', s_min3: '최근 3년 중 가장 적었던 소득', s_vol3: '최근 3년 소득 출렁임', age_to_nps: '국민연금 받기까지 남은 기간' };
const flabel = x => FLABEL[x.feature] || x.label;
function reasonText(f, P, up){""")

# ---------- 다음 걸음: 빚 안내 조건 ----------
rep("""  debt: { k: '빚', t: '빚을 조정하는 공적 제도 알아보기',""", """  debtcare: { k: '빚', t: '빚 관리 상담 받아 보기',
    todo: ['상환 계획, 대출, 채무조정 등 상황에 맞는 길을 안내받을 수 있어요', '어떤 길이 맞는지는 상담에서 함께 판단해요'],
    links: [['서민금융진흥원', 'https://www.kinfa.or.kr/']], tel: '서민금융콜센터 1397' },
  debt: { k: '빚', t: '빚을 조정하는 공적 제도 알아보기',""")
rep("""    if (k && x.effect > 0 && !(k === 'house' && !(P.owner && P.age >= 55)) && !(k === 'debt' && P.debt <= 0)) { prio.add(k); add(k, `모델이 꼽은 위험 이유 · ${x.label}. ${reasonText(x.feature, P, true)}`); } });""",
    """    let kk = k; if (k === 'debt') kk = P.debt_stress === 'overdue' ? 'debt' : P.debt_stress === 'tight' ? 'debtcare' : null;   // 빚은 상환이 어렵다고 답했을 때만
    if (kk && x.effect > 0 && !(kk === 'house' && !(P.owner && P.age >= 55))) { prio.add(kk); add(kk, `풀이에서 신경 쓸 부분으로 본 '${flabel(x)}'와 이어져요. ${reasonText(x.feature, P, true)}`); } });""")
rep("  if (ratio < 1) add('bokjiro', `지금 1인 기준 소득이 빈곤선의 ${ratio.toFixed(2)}배로 이미 아래쪽이에요. 받을 수 있는 복지부터 확인해 보세요.`);",
    "  if (ratio < 1) add('bokjiro', `지금 1인 기준 소득이 생활 기준선보다 낮아요(약 ${ratio.toFixed(2)}배). 받을 수 있는 지원부터 확인해 보세요.`);")
rep("  else if (ratio < 1.5) add('bokjiro', `지금 1인 기준 소득이 빈곤선의 ${ratio.toFixed(2)}배로 가까운 편이에요.`);",
    "  else if (ratio < 1.5) add('bokjiro', `지금 1인 기준 소득이 생활 기준선의 약 ${ratio.toFixed(2)}배로, 여유가 크지는 않아요.`);")
rep("  if (P.debt > 0 && debtX >= 1) add('debt', `남은 빚 ${fmt(P.debt)}만원이 연소득의 ${debtX.toFixed(1)}배예요.`);",
    """  if (P.debt > 0 && P.debt_stress === 'overdue') add('debt', '빚 갚기가 어렵거나 연체가 걱정된다고 답하셨어요. 혼자 버티기보다 공적 제도를 먼저 알아보세요.');
  else if (P.debt > 0 && P.debt_stress === 'tight') add('debtcare', `빚 갚기가 빠듯하다고 답하셨어요(남은 빚 ${fmt(P.debt)}만원). 연체가 되기 전에 상담을 받아 두면 선택지가 넓어요.`);
  else if (P.debt > 0 && P.debt_type === 'other' && P.debt_stress !== 'ok' && debtX >= 1) add('debtcare', `신용대출·카드 빚이 연소득의 ${debtX.toFixed(1)}배예요. 금리가 높은 빚이라면 미리 관리 방법을 알아 두면 좋아요.`);""")
rep("  if (r && r.eligible && r.band === 'high' && !r.abstain) add('bokjiro', '모델이 같은 나이대 위험 상위 20% 안으로 봤어요. 받을 수 있는 것부터 확인해 두면 좋아요.');",
    "  if (r && r.eligible && r.band === 'high' && !r.abstain) add('bokjiro', '2년 뒤 살림이 빠듯해질 신호가 여러 개 보였어요. 받을 수 있는 것부터 확인해 두면 마음이 편해요.');")

# ---------- 준비 중 문구 ----------
rep("'모델 서버가 연결되면 여기에 2년 뒤 위험 구간, 그렇게 본 이유 3가지, 확신이 없을 때의 \"판단 보류\"가 나와요.'",
    "'모델 서버가 연결되면 여기에 2년 뒤 풀이, 그렇게 본 이유 3가지, 확신이 없을 때의 \"판단 보류\"가 나와요.'")
rep("'모델 서버는 켜져 있지만 진단 기능은 아직 열리지 않았어요. 열리면 여기에 2년 뒤 위험 구간과 이유 3가지가 나와요.'",
    "'모델 서버는 켜져 있지만 풀이 기능은 아직 열리지 않았어요. 열리면 여기에 2년 뒤 풀이와 이유 3가지가 나와요.'")

# ---------- ② 결과 카드 새로 ----------
a = s.index('function drawML(r){'); b = s.index('/* ===== 단순 계산 풀이 ===== */')
s = s[:a] + r'''const LVL = p => p <= 20 ? '많은 편' : p <= 40 ? '조금 있는 편' : '적은 편';
function drawML(r){
  const box = $('mlBody'); box.innerHTML = ''; const P = lastP || {};
  if (!r.eligible) {
    const age = /50~69/.test(r.reason || '');
    mlMsg('풀이 대상 아님', age ? '2년 뒤 풀이는 1956~1975년생(50~69세)에게 맞춰 검증했어요. 아래 다음 걸음과 단순 셈은 그대로 참고하실 수 있어요.'
      : '지금 소득이 생활 기준선보다 낮아서, "지금은 괜찮은 분"의 2년 뒤를 보는 풀이 대상이 아니에요. 대신 받을 수 있는 지원부터 아래에서 확인해 보세요.');
    if (lastP) renderGuide(lastP, r); return;
  }
  $('mlTag').textContent = typeof r.model === 'string' ? (/S21$/.test(r.model) ? '건강 포함' : '기본') : '';
  lastRatio = typeof r.ratio_now === 'number' ? r.ratio_now : null;
  const reasons = Array.isArray(r.reasons) ? r.reasons.slice(0, 3) : [];
  // 1) 결론 한 줄
  const v = el('div', 'verdict'); const [lbl, cls] = r.abstain ? ['판단 보류', 'na'] : (BAND[r.band] || ['결과', 'na']);
  v.appendChild(el('span', 'badge ' + cls, lbl)); v.appendChild(el('span', 'muted', '2년 뒤 살림을 미리 본 풀이')); box.appendChild(v);
  const ratioTxt = lastRatio ? `약 ${lastRatio.toFixed(1)}배` : '';
  const head = r.abstain ? '신호가 양쪽으로 섞여 있어서, 이번에는 한쪽으로 단정하지 않을게요. 아래 이유를 함께 봐 주세요.'
    : r.band === 'high' ? `지금은 생활 기준선보다 여유가 있지만(${ratioTxt}), 2년 뒤 살림이 빠듯해질 수 있는 신호가 여러 개 보여요. 미리 알면 준비할 수 있어요.`
    : r.band === 'mid' ? '지금 형편은 괜찮은 편이에요. 다만 2년 뒤를 위해 미리 살펴 두면 좋은 부분이 조금 있어요.'
    : '지금 흐름이면 2년 뒤에도 크게 흔들리지 않을 가능성이 높아요.';
  const sum = el('div', 'sum'); sum.appendChild(el('p', 'head', head));
  const ul = el('ul'); const up = reasons.find(x => x.effect > 0), dn = reasons.find(x => x.effect < 0);
  const li = (k, x) => { const l = el('li'); l.appendChild(el('b', '', k + ' ' + flabel(x) + ' · ')); l.appendChild(document.createTextNode(reasonText(x.feature, P, x.effect > 0) || '')); ul.appendChild(l); };
  if (up) li('가장 신경 쓸 부분:', up);
  if (dn) li('든든한 부분:', dn);
  const l3 = el('li'); l3.appendChild(el('b', '', '그래서: ')); l3.appendChild(document.createTextNode("아래 '다음 걸음'에서 확인할 곳을 골라 두었어요.")); ul.appendChild(l3);
  sum.appendChild(ul); box.appendChild(sum);
  // 2) 이유 3가지
  if (reasons.length) {
    box.appendChild(el('p', 'mlsec-h', '이렇게 본 이유 (영향이 큰 순서)')).style.cssText = 'margin:18px 0 0;font-weight:700;font-size:14px';
    const bars = el('div', 'bars'); const mx = Math.max(...reasons.map(x => Math.abs(x.effect || 0)), 1e-9);
    reasons.forEach(x => {
      const b = el('div', 'bar'); b.innerHTML = '<div class="rowl"><span></span><span></span></div><div class="track"><div class="fill"></div></div>';
      const sp = b.querySelectorAll('.rowl span'); sp[0].textContent = flabel(x); sp[1].textContent = (x.effect || 0) >= 0 ? '신경 쓸 부분 ↑' : '든든한 부분 ↓';
      const rt = reasonText(x.feature, P, (x.effect || 0) >= 0); if (rt) b.appendChild(el('p', 'why', rt));
      const f = b.querySelector('.fill'); if ((x.effect || 0) < 0) f.classList.add('down');
      requestAnimationFrame(() => requestAnimationFrame(() => { f.style.width = Math.round(Math.abs(x.effect || 0) / mx * 100) + '%'; }));
      bars.appendChild(b);
    });
    box.appendChild(bars);
  }
  // 3) 근거는 접어 두기
  if (!r.abstain && typeof r.top_pct === 'number') {
    const more = el('details', 'more'); more.appendChild(el('summary', '', '이 풀이, 믿어도 될까요? (근거 자세히 보기)'));
    const bm = binOf(TEST.model, r.top_pct), on = Math.round(bm[2]);
    const s1 = el('div', 'mlsec'); s1.style.borderTop = '0'; s1.appendChild(el('h4', '', '비슷한 신호가 나온 분들은 실제로 어땠을까'));
    s1.appendChild(el('p', '', `이번 풀이와 비슷한 신호가 나온 분 100명 중 ${per100(bm[2])}이 2년 뒤 실제로 생활 기준선 아래로 여러 번 내려갔어요. 50~69세 전체로는 100명 중 약 ${Math.round(TEST.base)}명이에요.`));
    const d = el('div', 'dots'); d.setAttribute('role', 'img'); d.setAttribute('aria-label', `100명 중 ${per100(bm[2])}, 전체 평균 ${Math.round(TEST.base)}명`);
    for (let i = 0; i < 100; i++) { const c = el('i'); if (i < on) c.className = 'on'; if (i === Math.round(TEST.base) - 1) c.classList.add('avg'); d.appendChild(c); }
    s1.appendChild(d);
    const lg = el('div', 'legend'); lg.innerHTML = '<span><b style="background:var(--blood2)"></b>2년 뒤 살림이 빠듯해진 분</span><span><b style="outline:1.5px solid var(--text2)"></b>50~69세 전체 평균</span>'; s1.appendChild(lg);
    s1.appendChild(el('p', 'why', `한국복지패널에서 학습에 쓰지 않은 연도의 50~69세 ${TEST.n.toLocaleString('ko-KR')}명으로 확인한 결과예요. 내가 그중 한 명이 된다는 뜻은 아니고, 미리 준비하면 흐름은 바뀔 수 있어요.`));
    s1.appendChild(el('p', 'defn', '생활 기준선: 우리나라 가구 소득을 한 줄로 놓았을 때 한가운데 값의 절반(OECD 기준). 가구원 수를 반영해 1인 기준으로 맞춰 봐요.'));
    more.appendChild(s1);
    if (lastRatio) {
      const it = incomeTop(lastRatio), gap = it - r.top_pct;
      const s2 = el('div', 'mlsec'); s2.appendChild(el('h4', '', '소득 하나만 봤을 때와 무엇이 다른가'));
      const cm = el('div', 'cmp');
      const a = el('div'); a.appendChild(el('small', '', '지금 소득만 보면')); a.appendChild(el('strong', '', '신호 ' + LVL(it))); a.appendChild(el('p', 'why', `생활 기준선의 약 ${lastRatio.toFixed(2)}배`));
      const b = el('div', 'me'); b.appendChild(el('small', '', '네 기둥을 모두 보면 (흐름·일·가구·재산)')); b.appendChild(el('strong', '', '신호 ' + LVL(r.top_pct))); b.appendChild(el('p', 'why', `비슷한 분 100명 중 ${per100(bm[2])}`));
      cm.appendChild(a); cm.appendChild(b); s2.appendChild(cm);
      s2.appendChild(el('p', '', gap >= 10 ? '소득 수준만 보면 괜찮아 보여도, 소득의 흐름이나 일·가구 변화에서 신경 쓸 신호가 보였어요.'
        : gap <= -10 ? '소득 수준만 보면 빠듯해 보여도, 일·재산·연금 같은 다른 기둥이 받쳐 주고 있어요.'
        : '소득 수준과 다른 기둥이 비슷한 방향을 가리켜요.'));
      s2.appendChild(el('p', 'why', '같은 시험에서 신호가 가장 많다고 고른 분들 중 실제로 빠듯해진 분은, 소득만 보고 골랐을 때 100명 중 약 19명, 네 기둥을 다 보고 골랐을 때 약 22명이었어요.'));
      more.appendChild(s2);
    }
    box.appendChild(more);
  }
  if (r.abstain) box.appendChild(el('p', 'mlnote', '판단 보류: 신호가 양쪽으로 섞여 확신이 낮을 때는 결론 대신 이유만 보여 드려요.'));
  box.appendChild(el('p', 'mlnote', '이유는 모델이 이 답에서 풀이를 움직인 크기예요. 원인이라는 뜻은 아니고, 예측일 뿐 미래를 보장하지 않아요.'));
  if (lastP) renderGuide(lastP, r);
}

''' + s[b:]

# ---------- 단순 셈 카드 ----------
rep('<div class="card"><h3>지금 소득 vs 빈곤선 <span class="tag">단순 계산</span></h3>', '<div class="card"><h3>지금 소득과 생활 기준선 <span class="tag">단순 계산</span></h3>')
rep("$('rLineP').textContent = `가구원 ${P.hh_size}명 기준 1인당 월 ${fmt(eq)}만원 vs 빈곤선 월 ${fmt(LINE_YEAR / 12)}만원. ${ratio < 1 ? '이미 빈곤선 아래예요. 아래 제도 상담을 먼저 권해요.' : ratio < 1.5 ? '빈곤선과 가까운 편이에요.' : '빈곤선보다 여유가 있어요.'}`;",
    "$('rLineP').textContent = `가구원 ${P.hh_size}명 기준 1인당 월 ${fmt(eq)}만원, 생활 기준선은 월 ${fmt(LINE_YEAR / 12)}만원이에요. ${ratio < 1 ? '기준선보다 낮아요. 받을 수 있는 지원부터 확인해 보세요.' : ratio < 1.5 ? '기준선보다 조금 위예요.' : '기준선보다 여유가 있어요.'} (생활 기준선: 가구 소득 한가운데 값의 절반)`;")
rep("$('rDebtP').textContent = `부채 ${fmt(P.debt)}만원 = 연소득의 ${debtX !== null ? debtX.toFixed(1) : '–'}배. 재산에서 빚을 뺀 순자산은 ${fmt(net)}만원(금융 ${fmt(P.fin_asset)} + 부동산 ${fmt(P.real_asset)} − 부채).`;",
    "$('rDebtP').textContent = `남은 빚 ${fmt(P.debt)}만원 = 연소득의 ${debtX !== null ? debtX.toFixed(1) : '–'}배. 재산에서 빚을 뺀 순자산은 ${fmt(net)}만원(금융 ${fmt(P.fin_asset)} + 부동산 ${fmt(P.real_asset)} − 빚).${P.debt > 0 ? (P.debt_stress === 'tight' || P.debt_stress === 'overdue' ? ' 갚기가 빠듯하다면 아래 다음 걸음을 확인해 보세요.' : ' 빚의 크기보다 갚을 여력이 더 중요해요. 주택담보대출을 잘 갚고 있다면 이 숫자만으로 걱정할 일은 아니에요.') : ''}`;")
rep("  else if (debtX !== null && debtX >= 2) line = '\"빚이 연소득의 두 해 치를 넘어요. 은퇴 전에 그 무게를 조금씩 덜어 두면 노후가 한결 가벼워져요.\"';",
    "  else if (P.debt_stress === 'tight' || P.debt_stress === 'overdue') line = '\"빚 갚기가 빠듯하시군요. 혼자 버티지 마시고, 연체되기 전에 상담부터 받아 보세요.\"';")

left = re.findall(r'[^\n]{0,30}(?:빈곤|상위 \$|줄 세|위험을 올|위험을 낮)[^\n]{0,30}', s)
print('남은 표현:', left[:10])
open(out, 'w', encoding='utf-8').write(s)
