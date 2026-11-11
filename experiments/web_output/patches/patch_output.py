import sys, re
p = sys.argv[1]
s = open(p, encoding='utf-8').read()

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:60], s.count(old))
    s = s.replace(old, new)

# ---------- CSS ----------
CSS = r'''
/* 결과 보강: 실제 비율 · 소득만 vs 모델 · 이유 문장 · 다음 걸음 */
.mlsec{margin-top:18px;padding-top:16px;border-top:1px dashed var(--line2)}
.mlsec h4{margin:0 0 8px;font-size:14px;color:var(--text);font-weight:700}
.mlsec p{margin:6px 0 0;font-size:13.5px;color:var(--text2);line-height:1.65}
.dots{display:grid;grid-template-columns:repeat(20,1fr);gap:3px;max-width:340px;margin:10px 0 4px}
.dots i{display:block;aspect-ratio:1;border-radius:50%;background:rgba(255,255,255,.09)}
.dots i.on{background:var(--blood2);box-shadow:0 0 6px rgba(255,45,74,.55)}
.dots i.avg{outline:1px solid var(--gold);outline-offset:1px}
.legend{font-size:12px;color:var(--text3);display:flex;gap:14px;flex-wrap:wrap}
.legend b{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:0}
.cmp{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px}
.cmp>div{border:1px solid var(--line2);border-radius:12px;padding:10px 12px;background:rgba(255,255,255,.02)}
.cmp>div.me{border-color:rgba(255,45,74,.55);background:rgba(200,16,46,.08)}
.cmp small{display:block;font-size:12px;color:var(--text3)}
.cmp strong{font-family:var(--title);font-size:24px;font-weight:800}
.why{font-size:12.5px;color:var(--text3);margin:4px 0 0;line-height:1.55}
#guide{margin:0 0 22px}
#guide .glist{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.gcard{border:1px solid var(--line2);border-radius:16px;padding:16px 18px;background:var(--card);display:flex;flex-direction:column;gap:8px}
.gcard.prio{border-color:rgba(233,196,106,.55)}
.gcard .gk{font-size:12px;color:var(--gold)}
.gcard h4{margin:0;font-size:16px;color:var(--text)}
.gcard .gwhy{margin:0;font-size:13.5px;color:var(--text2);line-height:1.6}
.gcard ul{margin:0;padding-left:18px;font-size:13px;color:var(--text2);line-height:1.6}
.gcard .glinks{display:flex;flex-wrap:wrap;gap:8px;margin-top:auto;padding-top:4px}
.gcard .glinks a{font-size:13px;color:var(--text);text-decoration:none;border:1px solid var(--line2);border-radius:999px;padding:6px 12px;background:rgba(255,255,255,.03)}
.gcard .glinks a:hover,.gcard .glinks a:focus-visible{border-color:var(--blood2);color:#fff}
.gcard .tel{font-size:12.5px;color:var(--text3)}
.gnote{font-size:12.5px;color:var(--text3);margin:10px 0 0}
@media (max-width:640px){ #guide .glist{grid-template-columns:1fr} .cmp{grid-template-columns:1fr} }
'''
rep('.mlnote{font-size:12.5px;color:var(--text3);margin:12px 0 0}', '.mlnote{font-size:12.5px;color:var(--text3);margin:12px 0 0}' + CSS)

# ---------- markup: 다음 걸음 영역 ----------
rep('''<h3 class="subhead">네 기둥 단순 셈''', '''<section id="guide" aria-labelledby="guideH"><h3 class="subhead" id="guideH">아기씨가 가리키는 다음 걸음 <span class="tag">공식 사이트 안내</span></h3><div class="glist" id="gList"></div><p class="gnote">자격과 금액은 각 기관이 판단해요. 미리사주는 상담이나 금융상품을 연결하지 않고, 공공기관 공식 페이지로만 안내해요. 주소는 바뀔 수 있으니 열리지 않으면 기관 이름으로 찾아 주세요.</p></section>
  <h3 class="subhead">네 기둥 단순 셈''')

# ---------- JS ----------
JS = r'''
/* ===== 결과 보강용 집계 (한국복지패널 봉인 시험셋 4,984명, S20 모델. 개인 값 없음, 집계만) ===== */
const TEST = { n: 4984, base: 6.0,
  // 모델 위험 순위 구간별 '2년 뒤 반복 하락' 실제 비율(%)
  model: [[0,10,33.3],[10,20,10.6],[20,30,8.6],[30,40,3.2],[40,60,1.1],[60,80,0.4],[80,100,0.8]],
  // 지금 소득(빈곤선 대비 배수)만으로 줄 세웠을 때 구간별 실제 비율(%)
  income: [[0,10,23.5],[10,20,15.1],[20,30,8.0],[30,40,3.0],[40,60,3.4],[60,80,1.3],[80,100,0.7]],
  // 지금 소득 배수의 백분위 0~100 (낮을수록 위험 쪽)
  rq: [1.0003,1.021,1.041,1.0654,1.0848,1.1155,1.1349,1.1685,1.1887,1.2119,1.2351,1.2597,1.2799,1.2998,1.3276,1.3501,1.3744,1.4028,1.4166,1.4331,1.4586,1.4785,1.4971,1.5119,1.53,1.5539,1.5705,1.5862,1.6086,1.6348,1.6542,1.6708,1.6955,1.7197,1.7415,1.7556,1.7697,1.7906,1.8153,1.8374,1.8589,1.8792,1.903,1.9314,1.9502,1.9715,1.9904,2.0186,2.0368,2.054,2.0783,2.1032,2.1338,2.1591,2.1876,2.2063,2.2262,2.2508,2.2759,2.2985,2.3249,2.3467,2.3749,2.4047,2.4499,2.4822,2.508,2.5391,2.5686,2.5995,2.631,2.662,2.7018,2.7362,2.7764,2.8161,2.8467,2.8899,2.9199,2.9578,2.9991,3.0443,3.1074,3.1748,3.2277,3.2922,3.3817,3.4565,3.5177,3.6265,3.692,3.8145,3.9265,4.0478,4.2031,4.3889,4.5835,4.8662,5.3956,6.2664,20.7835] };
const binOf = (tbl, pct) => tbl.find(b => pct >= b[0] && pct < b[1]) || tbl[tbl.length - 1];
function incomeTop(r){ const q = TEST.rq; if (r <= q[0]) return 0; if (r >= q[100]) return 100;
  for (let i = 1; i <= 100; i++) if (r < q[i]) return (i - 1) + (r - q[i - 1]) / (q[i] - q[i - 1]); return 100; }
const per100 = v => v < 1 ? '1명 미만' : `약 ${Math.round(v)}명`;
function el(tag, cls, text){ const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }

/* 이유 하나를 '내 값'이 들어간 문장으로 */
function reasonText(f, P, up){
  const L = LINE_YEAR / 12, rr = (inc, h) => inc > 0 ? inc / Math.sqrt(h) / L : 0;
  const r0 = rr(P.income_now, P.hh_size), r1 = rr(P.income_1y, P.hh_size), r2 = rr(P.income_2y, P.hh_size_2y);
  const pc = (a, b) => b > 0 ? `${a >= b ? '+' : ''}${Math.round((a / b - 1) * 100)}%` : '–';
  const yr = P.income_now * 12, xr = v => yr > 0 ? (v / yr).toFixed(1) : '–';
  const npsLeft = -P.age_to_nps, job = { regular: '상용직', temp: '임시·일용직', self: '자영업', other: '그 밖의 일', none: '일 안 함' }[P.job_type];
  const T = {
    s_log_r: `지금 1인 기준 소득이 빈곤선의 약 ${r0.toFixed(2)}배예요.`,
    s_min3: `최근 3년 중 가장 낮았던 해의 소득이 빈곤선의 약 ${Math.min(r0, r1, r2).toFixed(2)}배였어요. 한 번 낮아졌던 기록은 다시 내려갈 가능성과 이어져요.`,
    s_d1: `1년 사이 가구 소득이 ${fmt(P.income_1y)} → ${fmt(P.income_now)}만원(${pc(P.income_now, P.income_1y)})으로 바뀌었어요.`,
    s_d2: `2년 사이 가구 소득이 ${fmt(P.income_2y)} → ${fmt(P.income_now)}만원(${pc(P.income_now, P.income_2y)})으로 바뀌었어요.`,
    s_vol3: `3년 소득이 ${fmt(P.income_2y)} → ${fmt(P.income_1y)} → ${fmt(P.income_now)}만원으로 ${up ? '출렁였어요' : '비교적 고르게 이어졌어요'}.`,
    hhsize: `함께 사는 가구원이 ${P.hh_size}명이에요.`,
    s_hhchg: P.hh_change_2y ? `2년 사이 가구원이 ${P.hh_change_2y > 0 ? '+' : ''}${P.hh_change_2y}명 바뀌었어요.` : '2년 사이 가구원 수가 그대로예요.',
    age: `지금 ${P.age}세예요.`, age_to_60: `60세까지 ${P.age_to_60 < 0 ? -P.age_to_60 + '년 남았어요' : '이미 지났어요'}.`,
    age_to_nps: npsLeft > 0 ? `국민연금 정상 개시까지 ${npsLeft}년 남았어요.` : '국민연금 정상 개시 나이가 지났어요.',
    female: `성별(${P.female ? '여성' : '남성'})에 따른 패널 속 평균적인 차이예요.`, married: `배우자가 ${P.married ? '있어요' : '없어요'}.`,
    edu3: `학력(${['고졸 미만', '고졸', '대졸 이상'][P.edu3]})에 따른 패널 속 평균적인 차이예요.`,
    x_pension_recv: `공적연금을 지금 ${P.pension_recv ? '받고 있어요' : '받지 않고 있어요'}.`,
    x_retire_pension: `퇴직연금이 ${P.retire_pension ? '있어요' : '없어요'}.`, x_private_pension: `개인연금이 ${P.private_pension ? '있어요' : '없어요'}.`,
    employed: `지금 ${P.employed ? '일하고 있어요' : '일하지 않고 있어요'}.`, s_emp_l1: `1년 전에는 ${P.employed_1y ? '일하고 있었어요' : '일하지 않았어요'}.`,
    s_emp_l2: `2년 전에는 ${P.employed_2y ? '일하고 있었어요' : '일하지 않았어요'}.`,
    s_lost: P.lost_job_2y ? '2년 전에는 일했는데 지금은 일하지 않아요.' : '최근 2년 안에 일을 그만두지 않았어요.',
    x_regular: `일의 형태: ${job}.`, x_temp_daily: `일의 형태: ${job}.`, x_selfemp: `일의 형태: ${job}.`,
    s_owner: `사는 집이 ${P.owner ? '자가예요' : '자가가 아니에요'}.`,
    s_fin_r: `금융자산 ${fmt(P.fin_asset)}만원, 연소득의 ${xr(P.fin_asset)}배예요.`, s_lg_fin: `금융자산이 ${fmt(P.fin_asset)}만원이에요.`,
    s_debt_r: `남은 빚 ${fmt(P.debt)}만원, 연소득의 ${xr(P.debt)}배예요.`, s_lg_debt: `남은 빚이 ${fmt(P.debt)}만원이에요.`,
    s_real_r: `부동산 ${fmt(P.real_asset)}만원, 연소득의 ${xr(P.real_asset)}배예요.`, s_lg_real: `부동산이 ${fmt(P.real_asset)}만원이에요.`,
    s_health: '건강 상태 답이 반영됐어요.',
  };
  return T[f] || '';
}

/* ===== 다음 걸음: 답(과 모델 이유)에 맞는 공식 사이트 ===== */
const SRC = {
  bokjiro: { k: '복지 확인', t: '받을 수 있는 복지, 미리 계산해 보기',
    todo: ['가구원 수·소득·재산을 넣어 받을 수 있는 복지서비스를 모의계산', '소득이 줄었다면 줄어든 지금 소득으로 다시 계산'],
    links: [['복지로 복지서비스 모의계산', 'https://www.bokjiro.go.kr/ssis-tbu/twatbz/mkclAsis/mkclPage.do']] },
  basic: { k: '연금', t: '기초연금 대상인지 확인하기',
    todo: ['만 65세 이상이고 소득인정액이 선정기준액 이하일 때 받는 연금', '복지로 온라인 또는 국민연금공단 지사에서 신청', '65세가 되기 2개월 전부터 국민연금공단이 안내를 보내요'],
    links: [['국민연금공단 기초연금 신청 안내', 'https://www.nps.or.kr/comm/pop/getOHAH0015P1.do']], tel: '국민연금 고객센터 1355' },
  csa: { k: '노후준비', t: '연금이 열리기 전, 노후준비 진단 받아 보기',
    todo: ['예상 연금액은 로그인 없이 모의계산', '노후준비 종합진단·재무진단으로 공백기 점검', '상담 예약도 같은 곳에서'],
    links: [['중앙노후준비지원센터', 'https://csa.nps.or.kr/ohkd/bspsctng/UHKD8001M0.do']], tel: '국민연금 고객센터 1355' },
  work: { k: '일', t: '다음 일과 직업훈련 찾아보기',
    todo: ['중장년 채용 정보와 직업훈련 과정 검색', '구직 등록 후 지원 제도 확인'],
    links: [['고용24', 'https://www.work24.go.kr/']] },
  house: { k: '집', t: '집을 담보로 한 주택연금 알아보기',
    todo: ['집에 살면서 평생 매달 연금을 받는 제도', '주요 조건: 부부 중 한 명이 만 55세 이상, 공시가격 12억원 이하 주택 (최신 기준은 공식 페이지에서)', '예상 월지급금을 먼저 조회'],
    links: [['한국주택금융공사 주택연금', 'https://www.hf.go.kr/ko/sub03/sub03_01_01_01.do']] },
  debt: { k: '빚', t: '빚을 조정하는 공적 제도 알아보기',
    todo: ['신용회복위원회 채무조정, 개인회생·파산 같은 제도가 있어요', '어떤 제도가 맞는지는 기관 상담에서 판단'],
    links: [['신용회복위원회', 'https://www.ccrs.or.kr/cms/com/index.do?MENU_ID=1720'], ['서민금융진흥원 채무조정 안내', 'https://www.kinfa.or.kr/financialLife/debtSettlementSystem.do'], ['복지로: 신용회복위원회 바로 알기', 'https://www.bokjiro.go.kr/ssis-tbu/cms/pc/news/promotion/1301736_1118.html']],
    tel: '서민금융콜센터 1397' },
};
const FEAT2SRC = { s_log_r: 'bokjiro', s_min3: 'bokjiro', s_d1: 'bokjiro', s_d2: 'bokjiro', s_vol3: 'bokjiro', hhsize: 'bokjiro', s_hhchg: 'bokjiro',
  employed: 'work', s_emp_l1: 'work', s_emp_l2: 'work', s_lost: 'work', x_temp_daily: 'work', x_regular: 'work', x_selfemp: 'work',
  x_pension_recv: 'csa', age_to_nps: 'csa', age_to_60: 'csa', age: 'csa', x_retire_pension: 'csa', x_private_pension: 'csa',
  s_debt_r: 'debt', s_lg_debt: 'debt', s_owner: 'house', s_real_r: 'house', s_lg_real: 'house', s_fin_r: 'csa', s_lg_fin: 'csa' };
function renderGuide(P, r){
  const ratio = r && r.ratio_now ? r.ratio_now : P.income_now / Math.sqrt(P.hh_size) / (LINE_YEAR / 12);
  const flow = P.income_2y > 0 ? P.income_now / P.income_2y - 1 : 0, debtX = P.income_now > 0 ? P.debt / (P.income_now * 12) : 0;
  const npsLeft = -P.age_to_nps, pct = v => `${Math.abs(Math.round(v * 100))}%`;
  const why = {}, prio = new Set(), add = (k, w) => { if (!why[k]) why[k] = w; };
  // 1) 모델이 '위험을 올림'으로 본 이유와 이어지는 곳을 먼저
  if (r && r.eligible && Array.isArray(r.reasons)) r.reasons.forEach(x => { const k = FEAT2SRC[x.feature];
    if (k && x.effect > 0 && !(k === 'house' && !(P.owner && P.age >= 55)) && !(k === 'debt' && P.debt <= 0)) { prio.add(k); add(k, `모델이 '${x.label}'을(를) 위험을 올린 이유로 꼽았어요. ${reasonText(x.feature, P, true)}`); } });
  // 2) 답으로 판단
  if (ratio < 1) add('bokjiro', `지금 1인 기준 소득이 빈곤선의 ${ratio.toFixed(2)}배로 이미 아래쪽이에요. 받을 수 있는 복지부터 확인해 보세요.`);
  else if (ratio < 1.5) add('bokjiro', `지금 1인 기준 소득이 빈곤선의 ${ratio.toFixed(2)}배로 가까운 편이에요.`);
  if (flow <= -0.15) add('bokjiro', `최근 2년 사이 가구 소득이 ${pct(flow)} 줄었어요.`);
  if (P.lost_job_2y) add('work', '2년 전에는 일했는데 지금은 일하지 않고 있어요.');
  else if (!P.employed && P.age < 65) add('work', `지금 일하지 않고 있고, ${npsLeft > 0 ? `국민연금이 열리기까지 ${npsLeft}년 남았어요` : '일할 길도 함께 볼 만해요'}.`);
  else if (P.job_type === 'temp') add('work', '임시·일용직은 일이 끊기기 쉬워요. 이어갈 일을 미리 알아 두면 좋아요.');
  if (P.debt > 0 && debtX >= 1) add('debt', `남은 빚 ${fmt(P.debt)}만원이 연소득의 ${debtX.toFixed(1)}배예요.`);
  if (P.age >= 63) add('basic', P.age >= 65 ? `만 ${P.age}세예요. 기초연금 대상인지 확인해 보세요.` : `만 65세까지 ${65 - P.age}년 남았어요. 미리 기준을 알아 두세요.`);
  if (!P.pension_recv && npsLeft > 0) add('csa', `국민연금이 열리기까지 ${npsLeft}년${!P.retire_pension && !P.private_pension ? ', 그 사이를 받칠 퇴직·개인연금이 없어요' : ' 남았어요'}.`);
  else if (!P.pension_recv) add('csa', '공적연금을 아직 받지 않고 있어요. 예상 연금액과 수령 시점을 확인해 보세요.');
  if (P.owner && P.age >= 55 && (ratio < 2 || (r && r.band === 'high'))) add('house', `자가에 살고 있고 만 ${P.age}세예요. 집을 팔지 않고 생활비를 보탤 길이 있어요.`);
  if (r && r.eligible && r.band === 'high' && !r.abstain) add('bokjiro', '모델이 같은 나이대 위험 상위 20% 안으로 봤어요. 받을 수 있는 것부터 확인해 두면 좋아요.');
  let keys = [...prio, ...Object.keys(why).filter(k => !prio.has(k))].slice(0, 4);
  if (!keys.length) { keys = ['csa']; why.csa = '지금은 크게 걸리는 곳이 없어요. 해마다 한 번 노후준비를 점검해 두면 좋아요.'; }
  const box = $('gList'); box.innerHTML = '';
  keys.forEach(k => { const s = SRC[k], c = el('article', 'gcard' + (prio.has(k) ? ' prio' : ''));
    c.appendChild(el('span', 'gk', (prio.has(k) ? '모델 이유와 연결 · ' : '내 답과 연결 · ') + s.k));
    c.appendChild(el('h4', '', s.t)); c.appendChild(el('p', 'gwhy', why[k]));
    const ul = el('ul'); s.todo.forEach(t => ul.appendChild(el('li', '', t))); c.appendChild(ul);
    const lk = el('div', 'glinks'); s.links.forEach(([n, u]) => { const a = el('a', '', n + ' ↗'); a.href = u; a.target = '_blank'; a.rel = 'noopener noreferrer'; lk.appendChild(a); }); c.appendChild(lk);
    if (s.tel) c.appendChild(el('span', 'tel', '전화 ' + s.tel));
    box.appendChild(c); });
}
let lastP = null;
'''
rep("let mlSeq = 0;", JS + "let mlSeq = 0;")

# drawML: 태그, 실제 비율, 소득만 vs 모델, 이유 문장, 각주
rep("$('mlTag').textContent = r.model && r.model.version ? r.model.version : '';",
    "$('mlTag').textContent = typeof r.model === 'string' ? (/S21$/.test(r.model) ? '건강 포함 모델' : '기본 모델') : (r.model && r.model.version) || '';")
rep("  box.appendChild(v);\n  if (r.abstain) {", r'''  box.appendChild(v);
  const P = lastP || {};
  if (!r.abstain && typeof r.top_pct === 'number') {
    const bm = binOf(TEST.model, r.top_pct), on = Math.round(bm[2]);
    const s1 = el('div', 'mlsec'); s1.appendChild(el('h4', '', '이 자리에 섰던 사람들은 실제로 어땠나'));
    s1.appendChild(el('p', '', `모델이 시험에서 상위 ${bm[0]}~${bm[1]}%로 줄 세운 사람 100명 중 ${per100(bm[2])}이 2년 뒤 실제로 빈곤선 아래로 반복해서 내려갔어요. 전체 평균은 100명 중 약 ${Math.round(TEST.base)}명이에요.`));
    const d = el('div', 'dots'); d.setAttribute('role', 'img'); d.setAttribute('aria-label', `100명 중 ${per100(bm[2])} 하락, 평균 ${Math.round(TEST.base)}명`);
    for (let i = 0; i < 100; i++) { const c = el('i'); if (i < on) c.className = 'on'; if (i === Math.round(TEST.base) - 1) c.classList.add('avg'); d.appendChild(c); }
    s1.appendChild(d);
    const lg = el('div', 'legend'); lg.innerHTML = '<span><b style="background:var(--blood2)"></b>2년 뒤 반복 하락</span><span><b style="outline:1px solid var(--gold)"></b>전체 평균 위치</span>'; s1.appendChild(lg);
    s1.appendChild(el('p', 'why', `한국복지패널에서 학습에 쓰지 않은 연도의 50~69세 ${TEST.n.toLocaleString('ko-KR')}명으로 시험한 결과예요. 그 사람들 중 한 명이 된다는 뜻은 아니에요.`));
    box.appendChild(s1);
    if (typeof r.ratio_now === 'number') {
      const it = incomeTop(r.ratio_now), bi = binOf(TEST.income, it), gap = it - r.top_pct;
      const s2 = el('div', 'mlsec'); s2.appendChild(el('h4', '', '지금 소득만 볼 때와 무엇이 다른가'));
      const cm = el('div', 'cmp');
      const a = el('div'); a.appendChild(el('small', '', '지금 소득만으로 줄 세우면')); a.appendChild(el('strong', '', `상위 ${Math.max(1, Math.round(it))}%`)); a.appendChild(el('p', 'why', `빈곤선의 ${r.ratio_now.toFixed(2)}배 · 이 자리 100명 중 ${per100(bi[2])} 하락`));
      const b = el('div', 'me'); b.appendChild(el('small', '', '미리사주 모델 (흐름·일·가구·재산까지)')); b.appendChild(el('strong', '', `상위 ${Math.max(1, Math.round(r.top_pct))}%`)); b.appendChild(el('p', 'why', `이 자리 100명 중 ${per100(bm[2])} 하락`));
      cm.appendChild(a); cm.appendChild(b); s2.appendChild(cm);
      s2.appendChild(el('p', '', gap >= 10 ? '소득 수준만 보면 괜찮아 보여도, 소득의 흐름이나 일·가구 변화에서 위험 신호가 보였어요. 아래 이유가 그 신호예요.'
        : gap <= -10 ? '소득 수준만 보면 빠듯해 보여도, 다른 조건(일, 재산, 연금 등)이 받쳐 주고 있어요. 아래 이유를 보면 무엇이 받쳐 주는지 알 수 있어요.'
        : '소득 수준과 다른 조건이 비슷한 방향을 가리켜요.'));
      s2.appendChild(el('p', 'why', '같은 시험에서 위험 상위 20%를 골랐을 때, 소득만으로 고르면 실제 하락자가 100명 중 약 19명, 모델로 고르면 약 22명이었어요(AUC 0.81 → 0.87).'));
      box.appendChild(s2);
    }
  }
  if (r.abstain) {''')
# 이유: 라벨 + 내 값 문장
rep("sp[0].textContent = x.label; sp[1].textContent = (x.effect || 0) >= 0 ? '위험을 올림 ↑' : '위험을 낮춤 ↓';",
    "sp[0].textContent = x.label; sp[1].textContent = (x.effect || 0) >= 0 ? '위험을 올림 ↑' : '위험을 낮춤 ↓';\n      const rt = lastP ? reasonText(x.feature, lastP, (x.effect || 0) >= 0) : ''; if (rt) b.appendChild(el('p', 'why', rt));")
rep("const h = document.createElement('p'); h.style.cssText = 'margin:16px 0 0;font-weight:700;font-size:14px'; h.textContent = '그렇게 본 이유';",
    "const h = document.createElement('p'); h.style.cssText = 'margin:18px 0 0;padding-top:16px;border-top:1px dashed var(--line2);font-weight:700;font-size:14px'; h.textContent = '그렇게 본 이유 (영향이 큰 순서 3가지)';")
rep("ft.textContent = (r.model && r.model.note) || '관측 자료로 학습한 예측이며 미래를 보장하지 않습니다.'; box.appendChild(ft);",
    "ft.textContent = '이유는 모델(LightGBM)이 이 답에서 점수를 움직인 크기(SHAP)예요. 원인이라는 뜻은 아니고, 예측일 뿐 미래를 보장하지 않아요.'; box.appendChild(ft);\n  if (lastP) renderGuide(lastP, r);")
# 대상 아님일 때도 안내 갱신
rep("mlMsg('대상 아님', r.reason + ' 아래 단순 셈과 제도 상담을 참고해 주세요.'); return; }",
    "mlMsg('대상 아님', r.reason + ' 아래 다음 걸음과 단순 셈을 참고해 주세요.'); if (lastP) renderGuide(lastP, r); return; }")
# render: 입력 저장 + 규칙 기반 안내 먼저
rep("  renderML(P);\n", "  lastP = P; renderGuide(P, null);\n  renderML(P);\n")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
