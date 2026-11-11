"""v3: ① 이유 막대 → '내 값 + 그래서 왜 중요한지' 문장 ② '몇 배' 대신 가구 기준 월 금액 ③ 기준선 아래인 사람도 지금 형편을 구체적으로 풀이"""
import sys
src, out = sys.argv[1:3]
s = open(src, encoding='utf-8').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:70], s.count(a)); s = s.replace(a, b)
def cut(a, b, new):
    global s
    i = s.index(a); j = s.index(b, i); s = s[:i] + new + s[j:]

# ---------- CSS ----------
rep('</style>\n</head>', '''
/* 이유: 막대 대신 문장 */
.rlist{display:grid;gap:10px;margin-top:10px}
.rs{border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:var(--card)}
.rs-top{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.rs-top b{font-size:15px;color:var(--text)}
.chip2{font-size:12px;font-weight:700;padding:3px 9px;border-radius:999px;border:1px solid}
.chip2.up{color:#8a5a12;background:rgba(212,166,55,.16);border-color:rgba(184,137,43,.5)}
.chip2.dn{color:#2f6a50;background:rgba(95,158,128,.14);border-color:rgba(95,158,128,.5)}
.rs-top .str{margin-left:auto;font-size:12px;color:var(--text3)}
.rs p{margin:6px 0 0;font-size:14px;color:var(--text2);line-height:1.65}
.rhelp{font-size:12.5px;color:var(--text3);margin:4px 0 0}
</style>
</head>''')

# ---------- 이유 문장: 사실 + 그래서 ----------
cut('function reasonText(f, P, up){', '/* ===== 다음 걸음', r'''const hhLine = n => LINE_YEAR / 12 * Math.sqrt(Math.max(1, n || 1));   // n인 가구 한 달 생활 기준선(만원)
const won = v => `${fmt(Math.abs(v))}만원`;
function margins(P){   // 해마다 '가구 소득 − 그 해 가구원 수 기준선'
  return [[P.income_now, P.hh_size, '지금'], [P.income_1y, P.hh_size, '1년 전'], [P.income_2y, P.hh_size_2y, '2년 전']]
    .filter(x => x[0] > 0).map(([m, n, t]) => ({ t, m, n, L: hhLine(n), d: m - hhLine(n) }));
}
function nowLine(P){
  const g = margins(P)[0]; if (!g) return '';
  return `지금 가구 소득 월 ${fmt(g.m)}만원은 ${g.n}인 가구 생활 기준선(월 ${fmt(g.L)}만원)보다 한 달에 ${won(g.d)} ${g.d >= 0 ? '많아요' : '적어요'}.`;
}
function reasonText(f, P, up){
  const ms = margins(P), g = ms[0] || { d: 0 }, lo = ms.reduce((a, b) => b.d < a.d ? b : a, g);
  const pc = (a, b) => b > 0 ? `${a >= b ? '+' : ''}${Math.round((a / b - 1) * 100)}%` : '–';
  const yr = P.income_now * 12, xr = v => yr > 0 ? (v / yr).toFixed(1) : '–';
  const npsLeft = -P.age_to_nps, job = { regular: '상용직', temp: '임시·일용직', self: '자영업', other: '그 밖의 일', none: '일 안 함' }[P.job_type];
  const T = {
    s_log_r: up ? `지금 기준선보다 한 달 ${won(g.d)} 여유예요. 여유 폭이 크지 않아서 소득이 조금만 줄어도 기준선 가까이 갈 수 있어요.`
                : `지금 기준선보다 한 달 ${won(g.d)} 여유가 있어요. 웬만한 변화는 버틸 수 있는 폭이에요.`,
    s_min3: up ? `최근 3년 중 가장 빠듯했던 때(${lo.t})는 기준선보다 한 달 ${won(lo.d)} ${lo.d >= 0 ? '여유' : '모자람'}이었어요. 한 번 출렁인 소득은 다시 출렁이기 쉬워요.`
               : `최근 3년 동안 가장 빠듯했던 때(${lo.t})에도 기준선보다 한 달 ${won(lo.d)} 여유가 있었어요. 꾸준히 버텨 온 흐름이에요.`,
    s_d1: `1년 사이 가구 소득이 ${fmt(P.income_1y)} → ${fmt(P.income_now)}만원(${pc(P.income_now, P.income_1y)})이 됐어요. ${up ? '줄어드는 흐름이 이어지면 여유가 빠르게 줄어요.' : '소득이 유지되거나 늘고 있어요.'}`,
    s_d2: `2년 사이 가구 소득이 ${fmt(P.income_2y)} → ${fmt(P.income_now)}만원(${pc(P.income_now, P.income_2y)})이 됐어요. ${up ? '줄어드는 흐름이 이어지면 여유가 빠르게 줄어요.' : '소득이 유지되거나 늘고 있어요.'}`,
    s_vol3: `3년 소득이 ${fmt(P.income_2y)} → ${fmt(P.income_1y)} → ${fmt(P.income_now)}만원이에요. ${up ? '해마다 크게 달라지는 소득은 다시 출렁이기 쉬워요.' : '고르게 이어져서 계획을 세우기 좋아요.'}`,
    hhsize: P.hh_size === 1 ? (up ? '혼자 살고 계세요. 혼자 버는 살림은 한 번 흔들리면 받쳐 줄 손이 적어요.' : '혼자 살고 계세요. 챙길 식구가 적어 지출 부담은 덜한 편이에요.')
                            : `${P.hh_size}명이 함께 살아요. ${up ? '식구가 많으면 같은 소득에서 한 사람 몫이 줄어요.' : '함께 버는 손이 있으면 한쪽이 흔들려도 버티기 쉬워요.'}`,
    s_hhchg: P.hh_change_2y ? `2년 사이 가구원이 ${Math.abs(P.hh_change_2y)}명 ${P.hh_change_2y > 0 ? '늘었어요' : '줄었어요'}. ${up ? '가구 구성이 바뀌면 버는 손과 쓰는 돈의 균형이 달라져요.' : '가구 변화가 살림을 크게 흔들지는 않았어요.'}` : '2년 사이 가구원 수가 그대로예요.',
    age: `지금 ${P.age}세예요. ${up ? '은퇴와 연금 사이, 소득이 바뀌기 쉬운 나이대예요.' : '이 나이대치고 안정적인 조건이에요.'}`,
    age_to_60: `${P.age_to_60 < 0 ? `60세까지 ${-P.age_to_60}년 남았어요.` : '60세를 넘었어요.'} ${up ? '정년 전후는 일이 끊기기 쉬운 시기예요.' : '아직 일할 시간이 넉넉한 편이에요.'}`,
    age_to_nps: npsLeft > 0 ? (up ? `국민연금이 열리기까지 ${npsLeft}년 남았어요. 그 사이 일이 끊기면 받쳐 줄 연금이 아직 없어요(공백기).` : `국민연금이 열리기까지 ${npsLeft}년, 아직 일할 수 있는 시기라 버틸 여지가 있어요.`)
                            : (up ? '국민연금 개시 나이는 지났지만, 연금만으로는 살림이 빠듯할 수 있는 나이대예요.' : '국민연금이 열리는 나이가 지나 연금이 소득을 받쳐 줄 수 있어요.'),
    female: '비슷한 조건의 분들에게서 보인 통계적인 경향이에요(성별). 개인 노력으로 바꿀 부분은 아니에요.',
    married: P.married ? (up ? '배우자가 있어요. 함께 쓰는 돈이 많은 시기라 영향이 있었어요.' : '배우자가 있어요. 버는 손이 둘일 수 있어 버팀목이 돼요.') : (up ? '배우자가 없어요. 혼자 버는 살림은 한 번 흔들리면 받쳐 줄 손이 적어요.' : '배우자가 없어도 지금 조건에서는 크게 흔들리지 않았어요.'),
    edu3: '비슷한 조건의 분들에게서 보인 통계적인 경향이에요(학력). 개인 노력으로 바꿀 부분은 아니에요.',
    x_pension_recv: P.pension_recv ? (up ? '공적연금을 받고 있지만 금액이 충분한지 확인해 볼 만해요.' : '공적연금을 받고 있어서 소득의 바닥을 받쳐 줘요.') : (up ? '아직 받는 공적연금이 없어요. 일 소득이 끊기면 대신할 소득이 없어요.' : '아직 연금을 받지 않아도 지금은 일 소득으로 버티고 있어요.'),
    x_retire_pension: P.retire_pension ? '퇴직연금이 있어요. 은퇴 뒤 소득을 받쳐 줄 수 있어요.' : '퇴직연금이 없어요. 은퇴 뒤 받쳐 줄 곳이 하나 적어요.',
    x_private_pension: P.private_pension ? '개인연금이 있어요. 은퇴 뒤 소득을 받쳐 줄 수 있어요.' : '개인연금이 없어요. 은퇴 뒤 받쳐 줄 곳이 하나 적어요.',
    employed: P.employed ? (up ? '지금 일하고 있지만 일의 형태나 나이상 이어 가기 어려울 수 있어요.' : '지금 일하고 있어서 소득이 꾸준히 들어와요.') : '지금 일하지 않고 있어요. 일 소득이 없으면 다른 소득에 기대야 해요.',
    s_emp_l1: `1년 전에는 ${P.employed_1y ? '일하고 있었어요' : '일하지 않았어요'}. ${up ? '최근 일의 변화가 소득 흐름에 영향을 줄 수 있어요.' : '일의 흐름이 이어지고 있어요.'}`,
    s_emp_l2: `2년 전에는 ${P.employed_2y ? '일하고 있었어요' : '일하지 않았어요'}. ${up ? '최근 일의 변화가 소득 흐름에 영향을 줄 수 있어요.' : '일의 흐름이 이어지고 있어요.'}`,
    s_lost: P.lost_job_2y ? '2년 전에는 일했는데 지금은 일하지 않아요. 일이 끊긴 직후는 소득이 크게 줄기 쉬운 때예요.' : '최근 2년 안에 일을 그만두지 않았어요. 일이 이어지는 건 큰 버팀목이에요.',
    x_regular: `일의 형태: ${job}. ${up ? '' : '고용이 비교적 안정적인 형태예요.'}`, x_temp_daily: `일의 형태: ${job}. ${up ? '일이 끊기기 쉬운 형태라 소득이 흔들릴 수 있어요.' : ''}`,
    x_selfemp: `일의 형태: ${job}. ${up ? '경기에 따라 소득이 크게 달라질 수 있어요.' : '내 일을 이어 갈 수 있는 형태예요.'}`,
    s_owner: P.owner ? (up ? '자가에 살고 있어요. 집값에 비해 손에 쥔 현금은 적을 수 있어요.' : '자가에 살고 있어서 월세 같은 주거비 부담이 적어요.') : (up ? '자가가 아니라 주거비가 계속 나가요.' : '자가가 아니어도 지금 조건에서는 크게 흔들리지 않았어요.'),
    s_fin_r: `금융자산 ${fmt(P.fin_asset)}만원, 연소득의 ${xr(P.fin_asset)}배예요. ${up ? '급할 때 꺼내 쓸 돈이 적은 편이에요.' : '급할 때 버팀목이 돼요.'}`,
    s_lg_fin: `금융자산이 ${fmt(P.fin_asset)}만원이에요. ${up ? '급할 때 꺼내 쓸 돈이 적은 편이에요.' : '급할 때 버팀목이 돼요.'}`,
    s_debt_r: `남은 빚 ${fmt(P.debt)}만원, 연소득의 ${xr(P.debt)}배예요. ${up ? '갚는 돈이 소득을 줄일 수 있어요.' : '빚 부담이 크지 않아요.'}${debtNote(P)}`,
    s_lg_debt: `남은 빚이 ${fmt(P.debt)}만원이에요. ${up ? '갚는 돈이 소득을 줄일 수 있어요.' : '빚 부담이 크지 않아요.'}${debtNote(P)}`,
    s_real_r: `부동산 ${fmt(P.real_asset)}만원, 연소득의 ${xr(P.real_asset)}배예요. ${up ? '부동산은 바로 생활비로 쓰기 어려워요.' : '필요할 때 기댈 곳이 있어요(예: 주택연금).'}`,
    s_lg_real: `부동산이 ${fmt(P.real_asset)}만원이에요. ${up ? '부동산은 바로 생활비로 쓰기 어려워요.' : '필요할 때 기댈 곳이 있어요(예: 주택연금).'}`,
    s_health: up ? '건강 상태가 일과 소득에 영향을 줄 수 있어요.' : '건강한 편이라 일을 이어 가는 데 버팀목이 돼요.',
  };
  return (T[f] || '').trim();
}

''')

# ---------- 결과: 대상 아님 / 결론 / 이유 ----------
cut("  if (!r.eligible) {\n    const age = /50~69/.test(r.reason || '');", "  $('mlTag').textContent = typeof r.model", r'''  if (!r.eligible) {
    const age = /50~69/.test(r.reason || '');
    if (age) { mlMsg('풀이 대상 아님', '2년 뒤 풀이는 1956~1975년생(50~69세)에게 맞춰 검증했어요. ' + nowLine(P) + ' 아래 다음 걸음과 단순 셈은 그대로 참고하실 수 있어요.'); if (lastP) renderGuide(lastP, r); return; }
    // 이미 기준선 아래: 2년 뒤 숫자 예측 대신 '지금 형편'을 구체적으로
    $('mlTag').textContent = '지금 형편 풀이';
    const ms = margins(P), below = ms.filter(x => x.d < 0).length, flow = P.income_2y > 0 ? P.income_now / P.income_2y - 1 : null;
    const v = el('div', 'verdict'); v.appendChild(el('span', 'badge high', '지금 먼저 챙길 운')); v.appendChild(el('span', 'muted', '지금 형편을 숫자로 본 풀이')); box.appendChild(v);
    const sum = el('div', 'sum'); sum.appendChild(el('p', 'head', nowLine(P) + ' 지금은 2년 뒤를 걱정하기보다, 받을 수 있는 지원부터 챙기는 게 먼저예요.'));
    const ul = el('ul');
    const li = (k, t) => { const l = el('li'); l.appendChild(el('b', '', k + ' ')); l.appendChild(document.createTextNode(t)); ul.appendChild(l); };
    li('얼마나 모자라나:', `한 달 ${won(ms[0].d)}, 1년이면 약 ${won(ms[0].d * 12)}이에요.`);
    li('얼마나 이어졌나:', ms.length > 1 ? `최근 3년 중 ${below}번(${ms.filter(x => x.d < 0).map(x => x.t).join('·')}) 기준선 아래였어요.${below === ms.length ? ' 한동안 이어진 상황이라 혼자 버티기보다 지원 제도를 꼭 확인해 보세요.' : ' 최근에 내려온 상황이에요.'}` : '지난 소득을 적지 않아 흐름은 볼 수 없었어요.');
    if (flow !== null) li('소득 흐름:', `2년 전 월 ${fmt(P.income_2y)}만원 → 지금 월 ${fmt(P.income_now)}만원(${flow >= 0 ? '+' : ''}${Math.round(flow * 100)}%).`);
    li('그래서:', "아래 '다음 걸음'에 지금 바로 확인할 지원을 골라 두었어요.");
    sum.appendChild(ul); box.appendChild(sum);
    box.appendChild(el('p', 'mlnote', '2년 뒤 예측 모델은 "지금은 기준선 위에 있는 분"의 자료로 학습했어요. 이미 기준선 아래인 경우에는 맞지 않는 숫자를 드리지 않으려고, 예측 대신 지금 형편을 풀이해 드려요.'));
    box.appendChild(el('p', 'defn', '생활 기준선: 우리나라 가구 소득을 한 줄로 놓았을 때 한가운데 값의 절반(OECD 기준)을 가구원 수에 맞춘 금액이에요.'));
    if (lastP) renderGuide(lastP, r); return;
  }
''')
rep("""  const ratioTxt = lastRatio ? `약 ${lastRatio.toFixed(1)}배` : '';
  const head = r.abstain ? '신호가 양쪽으로 섞여 있어서, 이번에는 한쪽으로 단정하지 않을게요. 아래 이유를 함께 봐 주세요.'
    : r.band === 'high' ? `지금은 생활 기준선보다 여유가 있지만(${ratioTxt}), 2년 뒤 살림이 빠듯해질 수 있는 신호가 여러 개 보여요. 미리 알면 준비할 수 있어요.`
    : r.band === 'mid' ? '지금 형편은 괜찮은 편이에요. 다만 2년 뒤를 위해 미리 살펴 두면 좋은 부분이 조금 있어요.'
    : '지금 흐름이면 2년 뒤에도 크게 흔들리지 않을 가능성이 높아요.';""",
"""  const nl = nowLine(P) + ' ';
  const head = r.abstain ? nl + '신경 쓸 신호와 든든한 신호가 섞여 있어서, 2년 뒤는 이번에 한쪽으로 단정하지 않을게요.'
    : r.band === 'high' ? nl + '그런데 소득 흐름과 일·가구 상황에서 신경 쓸 신호가 여러 개 보여서, 2년 안에 이 여유가 사라질 수 있어요. 미리 알면 준비할 수 있어요.'
    : r.band === 'mid' ? nl + '지금 형편은 괜찮은 편이지만, 2년 뒤를 위해 미리 챙겨 두면 좋은 부분이 조금 있어요.'
    : nl + '지금 흐름이면 2년 뒤에도 크게 흔들리지 않을 가능성이 높아요.';""")
cut("  // 2) 이유 3가지\n", "  // 3) 근거는 접어 두기", r'''  // 2) 이유 3가지: 막대 대신 '내 값 + 그래서'
  if (reasons.length) {
    box.appendChild(el('p', '', '이렇게 본 이유 3가지')).style.cssText = 'margin:18px 0 0;font-weight:700;font-size:14px';
    box.appendChild(el('p', 'rhelp', "'신경 쓸 부분'은 2년 뒤를 더 빠듯하게, '든든한 부분'은 덜 빠듯하게 만드는 쪽으로 작용했어요. 영향이 큰 것부터 보여 드려요."));
    const list = el('div', 'rlist'); const mx = Math.max(...reasons.map(x => Math.abs(x.effect || 0)), 1e-9);
    reasons.forEach(x => {
      const upx = (x.effect || 0) >= 0, k = Math.abs(x.effect || 0) / mx;
      const c = el('div', 'rs'), t = el('div', 'rs-top');
      t.appendChild(el('span', 'chip2 ' + (upx ? 'up' : 'dn'), upx ? '신경 쓸 부분' : '든든한 부분'));
      t.appendChild(el('b', '', flabel(x))); t.appendChild(el('span', 'str', '영향 ' + (k >= .66 ? '큼' : k >= .33 ? '중간' : '작음')));
      c.appendChild(t); const rt = reasonText(x.feature, P, upx); if (rt) c.appendChild(el('p', '', rt));
      list.appendChild(c);
    });
    box.appendChild(list);
  }
''')

# ---------- 단순 셈: 몇 배 → 월 금액 ----------
rep("  $('rLine').innerHTML = `${ratio.toFixed(2)}<small>배</small>`;",
    "  const gL = hhLine(P.hh_size), gd = P.income_now - gL;\n  $('rLine').innerHTML = `${gd >= 0 ? '+' : '−'}${fmt(Math.abs(gd))}<small>만원/월</small>`;")
rep("$('rLineP').textContent = `가구원 ${P.hh_size}명 기준 1인당 월 ${fmt(eq)}만원, 생활 기준선은 월 ${fmt(LINE_YEAR / 12)}만원이에요. ${ratio < 1 ? '기준선보다 낮아요. 받을 수 있는 지원부터 확인해 보세요.' : ratio < 1.5 ? '기준선보다 조금 위예요.' : '기준선보다 여유가 있어요.'} (생활 기준선: 가구 소득 한가운데 값의 절반)`;",
    "$('rLineP').textContent = `가구 소득 월 ${fmt(P.income_now)}만원, ${P.hh_size}인 가구 생활 기준선 월 ${fmt(gL)}만원. ${gd < 0 ? `한 달에 ${fmt(-gd)}만원 모자라요. 받을 수 있는 지원부터 확인해 보세요.` : ratio < 1.5 ? `한 달에 ${fmt(gd)}만원 여유가 있지만 폭이 크지는 않아요.` : `한 달에 ${fmt(gd)}만원 여유가 있어요.`} (생활 기준선: 가구 소득 한가운데 값의 절반을 가구원 수에 맞춘 금액)`;")
open(out, 'w', encoding='utf-8').write(s); print('ok')
