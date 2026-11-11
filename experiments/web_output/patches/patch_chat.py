"""프론트 수정: ① 챗봇 교체(대화로 기둥 채우기 → [풀이 보러 가기]) ② 결과 창 '네 기둥' → '당신의 기둥'
③ 100명 점 그림: 내 구간과 전체 평균을 두 줄로, 1명 미만도 보이게 ④ 판단 보류 설명 ⑤ 결과 전 아기씨 한마디가 결과와 어긋나지 않게"""
import sys, re
src, out = sys.argv[1:3]
s = open(src, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)


# ---------- ② 결과 창 문구 ----------
rep('<small>노후 사주 풀이</small>네 기둥을 읽었어요', '<small>노후 사주 풀이</small>당신의 기둥을 읽었어요')
rep('<h3 class="subhead">네 기둥 단순 셈', '<h3 class="subhead">당신의 기둥 단순 셈')
rep("el('small', '', '네 기둥을 모두 보면 (흐름·일·가구·재산)')", "el('small', '', '당신의 기둥을 모두 보면 (흐름·일·가구·재산)')")
rep('지금 소득 하나만 볼 때보다 네 기둥을 다 볼 때', '지금 소득 하나만 볼 때보다 기둥을 모두 볼 때')
rep('소득만 보고 골랐을 때 100명 중 약 19명, 네 기둥을 다 보고 골랐을 때 약 22명', '소득만 보고 골랐을 때 100명 중 약 19명, 기둥을 모두 보고 골랐을 때 약 22명')

# ---------- ⑤ 아기씨 한마디: 결과가 나오기 전 기본 문장은 중립, '든든' 문장은 결과가 낮음일 때만 ----------
rep("""  else line = '"네 기둥이 든든하게 서 있어요. 그래도 운은 해마다 바뀌니, 한 해에 한 번은 다시 살펴봐요."';
  $('oracle').textContent = line;""",
    """  else line = '"당신의 기둥을 차례로 읽었어요. 운은 해마다 바뀌니, 한 해에 한 번은 다시 살펴봐요."';
  $('oracle').textContent = line; $('oracle').dataset.def = line.startsWith('"당신의 기둥을 차례로') ? '1' : '0';""")
rep("  if (r.mode === 'below') return drawBelow(r);",
    """  if (r.mode === 'below') return drawBelow(r);
  if (!r.abstain && r.band === 'low' && $('oracle').dataset.def === '1') $('oracle').textContent = '"당신의 기둥이 든든하게 서 있어요. 그래도 운은 해마다 바뀌니, 한 해에 한 번은 다시 살펴봐요."';""")

# ---------- ③ 100명 점 그림 ----------
rep("const per100 = v => v < 1 ? '1명 미만' : `약 ${Math.round(v)}명`;",
    """const per100 = v => v < 1 ? '1명 미만' : `약 ${Math.round(v)}명`;
// 100명 점 그림 두 줄: 위 = 이번 풀이와 비슷한 분, 아래 = 전체 평균. 소수점 아래는 마지막 점을 그만큼만 칠해 1명 미만도 보이게
function dotRow(rate, cls, label){
  const w = el('div', 'dotrow'); w.appendChild(el('span', 'dl', label));
  const d = el('div', 'dots'); d.setAttribute('role', 'img'); d.setAttribute('aria-label', `${label}: 100명 중 ${per100(rate)}`);
  const full = Math.floor(rate + 1e-9), frac = rate - full;
  for (let i = 0; i < 100; i++) { const c = el('i');
    if (i < full) c.className = cls;
    else if (i === full && frac >= 0.05) { c.className = cls + ' part'; c.style.setProperty('--p', Math.round(frac * 360) + 'deg'); }
    d.appendChild(c); }
  w.appendChild(d); w.appendChild(el('b', 'dn', per100(rate))); return w;
}
function dotPair(rate, base, cls, mine, all){ const g = el('div', 'dotpair'); g.appendChild(dotRow(rate, cls, mine)); g.appendChild(dotRow(base, cls + ' avgc', all)); return g; }""")
rep("""    const d = el('div', 'dots'); d.setAttribute('role', 'img'); d.setAttribute('aria-label', `100명 중 ${per100(bb[2])} 다시 올라섬, 전체 ${Math.round(TESTB.up)}명`);
    for (let i = 0; i < 100; i++) { const c = el('i'); if (i < on) c.className = 'on up'; if (i === Math.round(TESTB.up) - 1) c.classList.add('avg'); d.appendChild(c); }
    s1.appendChild(d);
    const lg = el('div', 'legend'); lg.innerHTML = '<span><b style="background:var(--ok)"></b>2년 안에 다시 올라선 분</span><span><b style="outline:1.5px solid var(--text2)"></b>전체 평균</span>'; s1.appendChild(lg);""",
    """    s1.appendChild(dotPair(bb[2], TESTB.up, 'on up', '비슷한 신호', '전체 평균'));
    const lg = el('div', 'legend'); lg.innerHTML = '<span><b style="background:var(--ok)"></b>2년 안에 다시 올라선 분 (100명 중)</span>'; s1.appendChild(lg);""")
rep("""    const d = el('div', 'dots'); d.setAttribute('role', 'img'); d.setAttribute('aria-label', `100명 중 ${per100(bm[2])}, 전체 평균 ${Math.round(TEST.base)}명`);
    for (let i = 0; i < 100; i++) { const c = el('i'); if (i < on) c.className = 'on'; if (i === Math.round(TEST.base) - 1) c.classList.add('avg'); d.appendChild(c); }
    s1.appendChild(d);
    const lg = el('div', 'legend'); lg.innerHTML = '<span><b style="background:var(--blood2)"></b>2년 뒤 살림이 빠듯해진 분</span><span><b style="outline:1.5px solid var(--text2)"></b>50~69세 전체 평균</span>'; s1.appendChild(lg);""",
    """    s1.appendChild(dotPair(bm[2], TEST.base, 'on', '비슷한 신호', '50~69세 전체'));
    const lg = el('div', 'legend'); lg.innerHTML = '<span><b style="background:var(--blood2)"></b>2년 뒤 살림이 빠듯해진 분 (100명 중)</span>'; s1.appendChild(lg);""")
rep(".dots i.avg{outline:1.5px solid var(--text2);outline-offset:1px}",
    """.dots i.avg{outline:1.5px solid var(--text2);outline-offset:1px}
.dotpair{display:flex;flex-direction:column;gap:8px;margin:10px 0 6px}
.dotrow{display:grid;grid-template-columns:76px minmax(0,340px) auto;align-items:center;gap:10px}
.dotrow .dl{font-size:12.5px;color:var(--text2);font-weight:600}
.dotrow .dn{font-size:13px;color:var(--text);white-space:nowrap}
.dotrow .dots{margin:0}
.dots i.on.avgc{background:#c8b58e;box-shadow:none}
.dots i.on.up.avgc{background:#a9cbb9;box-shadow:none}
.dots i.part{background:conic-gradient(var(--blood2) var(--p),rgba(120,92,40,.12) 0);box-shadow:none}
.dots i.up.part{background:conic-gradient(var(--ok) var(--p),rgba(120,92,40,.12) 0)}
.dots i.avgc.part{background:conic-gradient(#c8b58e var(--p),rgba(120,92,40,.12) 0)}
.dots i.up.avgc.part{background:conic-gradient(#a9cbb9 var(--p),rgba(120,92,40,.12) 0)}
@media (max-width:480px){ .dotrow{grid-template-columns:1fr auto} .dotrow .dl{grid-column:1/-1} }""")
s = s.replace("const bb = binOf(TESTB.bins, r.top_pct), on = Math.round(bb[2]);", "const bb = binOf(TESTB.bins, r.top_pct);")
s = s.replace("const bm = binOf(TEST.model, r.top_pct), on = Math.round(bm[2]);", "const bm = binOf(TEST.model, r.top_pct);")

# ---------- ④ 판단 보류 설명 ----------
rep("  if (r.abstain) box.appendChild(el('p', 'mlnote', '판단 보류: 신호가 양쪽으로 섞여 확신이 낮을 때는 결론 대신 이유만 보여 드려요.'));",
    "  if (r.abstain) box.appendChild(el('p', 'mlnote', ABSTAIN_NOTE));", n=2)
rep("const BAND = {", """const ABSTAIN_NOTE = "판단 보류: 다른 결과 이름(예: '먼저 살펴볼 운')은 비슷한 분들 사이에서 신호가 얼마나 많은지, 즉 순위를 말해요. 판단 보류는 순위와 별개로 모델이 얼마나 확신하는지를 말해요. 신경 쓸 신호와 든든한 신호가 함께 커서 2년 뒤를 한쪽으로 확신하기 어려우면, 결론 대신 이유만 보여 드려요.";
const BAND = {""")

# ---------- ① 챗봇 ----------
a = s.index('/* ===== 상담 챗봇: 프론트 → CHAT_BASE/chat → Claude. API 키는 서버에만 있음 ===== */')
b = s.index('/* ===== 마법진 눈금 ===== */')
s = s[:a] + open(sys.argv[3], encoding='utf-8').read().rstrip() + '\n\n' + s[b:]
rep('<div><b>아기씨에게 묻기</b><div class="sub">노후 소득·연금·제도에 대해 물어보세요</div></div>',
    '<div><b>아기씨에게 묻기</b><div class="sub">대화로 기둥 채우기 · 사이트 안내 · 연금·제도 설명</div></div>')
rep('placeholder="예: 은퇴하고 연금 받기 전까지 어떻게 버티나요?"', 'placeholder="예: 1966년생 여자예요 / 결과 화면은 어떻게 봐요?"')
rep(".cb-note{", """.cb-prog{padding:8px 16px;border-bottom:1px solid var(--line);font-size:12.5px;color:var(--text2);display:flex;align-items:center;gap:10px}
.cb-prog[hidden]{display:none}
.cb-prog .bar{flex:1;height:6px;border-radius:6px;background:rgba(120,92,40,.12);overflow:hidden}
.cb-prog .bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--blood),var(--blood2));transition:width .5s}
.cb-go{align-self:stretch;border:1px solid rgba(212,166,55,.5);background:#fffaf0;border-radius:14px;padding:12px;display:flex;flex-direction:column;gap:8px}
.cb-go p{margin:0;font-size:13.5px;color:var(--text)}
.cb-go .row{display:flex;gap:8px;flex-wrap:wrap}
.cb-go button{border:0;border-radius:12px;padding:10px 14px;font-weight:700;cursor:pointer;font-size:14px}
.cb-go .main{background:#9a7020;color:#fff;flex:1}
.cb-go .sub2{background:transparent;border:1px solid var(--line2);color:var(--text2)}
.cb-note{""")
open(out, 'w', encoding='utf-8').write(s); print('ok')
