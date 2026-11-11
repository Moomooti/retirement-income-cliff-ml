"""v4: 기준선 아래 사용자(mode='below')에게 B20 모델 결과 – 지금 형편 + 2년 뒤 다시 올라설 가능성"""
import sys
src, out = sys.argv[1:3]
s = open(src, encoding='utf-8').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:70], s.count(a)); s = s.replace(a, b)

# 시험 집계 (B20 봉인 시험 1,131명, 구간별 '2년 안에 다시 올라선' 비율 %)
rep("const binOf = (tbl, pct) =>", """const TESTB = { n: 1131, up: 36.2, bins: [[0,20,3.5],[20,40,14.2],[40,60,37.2],[60,80,54.0],[80,100,72.2]] };
const binOf = (tbl, pct) =>""")

# 이유 문장: 기준선 아래일 때 지금 소득
rep("    s_log_r: up ? `지금 기준선보다 한 달 ${won(g.d)} 여유가 있어요. 같은 나이대와 비교하면 넉넉한 폭은 아니라, 소득이 줄면 영향을 받기 쉬워요.`",
    """    s_log_r: g.d < 0 ? (up ? `지금 기준선보다 한 달 ${won(g.d)} 모자라요. 모자란 폭이 클수록 다시 올라서기까지 시간이 걸려요.` : `지금 기준선보다 한 달 ${won(g.d)} 모자라지만, 폭이 크지 않아 다시 올라설 여지가 있어요.`)
           : up ? `지금 기준선보다 한 달 ${won(g.d)} 여유가 있어요. 같은 나이대와 비교하면 넉넉한 폭은 아니라, 소득이 줄면 영향을 받기 쉬워요.`""")

# 다음 걸음: 기준선 아래 모드에서는 '빠듯해질 신호' 문장 대신
rep("  if (r && r.eligible && r.band === 'high' && !r.abstain) add('bokjiro',",
    "  if (r && r.eligible && r.mode === 'below') add('bokjiro', '지금 소득이 기준선 아래예요. 받을 수 있는 지원부터 확인해 두면 다시 올라서는 데 힘이 돼요.');\n  if (r && r.eligible && r.mode !== 'below' && r.band === 'high' && !r.abstain) add('bokjiro',")

# 결과 카드: below 모드
rep("  $('mlTag').textContent = typeof r.model === 'string' ? (/S21$/.test(r.model) ? '건강 포함' : '기본') : '';",
    "  if (r.mode === 'below') return drawBelow(r);\n  $('mlTag').textContent = typeof r.model === 'string' ? (/S21$/.test(r.model) ? '건강 포함' : '기본') : '';")
rep("const LVL = p =>", r'''function drawBelow(r){
  const box = $('mlBody'); box.innerHTML = ''; const P = lastP || {};
  $('mlTag').textContent = '기준선 아래 풀이';
  lastRatio = typeof r.ratio_now === 'number' ? r.ratio_now : null;
  const reasons = Array.isArray(r.reasons) ? r.reasons.slice(0, 3) : [];
  const BANDB = { high: ['지금 먼저 챙길 운', 'high'], mid: ['갈림길의 운', 'mid'], low: ['다시 일어설 기운', 'low'] };
  const [lbl, cls] = r.abstain ? ['판단 보류', 'na'] : (BANDB[r.band] || ['결과', 'na']);
  const v = el('div', 'verdict'); v.appendChild(el('span', 'badge ' + cls, lbl)); v.appendChild(el('span', 'muted', '지금 형편과 2년 뒤를 함께 본 풀이')); box.appendChild(v);
  const head = nowLine(P) + ' ' + (r.abstain ? '다시 올라설 신호와 머물 신호가 섞여 있어서, 2년 뒤는 한쪽으로 단정하지 않을게요. 지금은 받을 수 있는 지원부터 챙겨 두세요.'
    : r.band === 'high' ? '2년 뒤에도 이 상황이 이어질 신호가 많아요. 혼자 버티기보다 받을 수 있는 지원부터 챙기는 게 먼저예요.'
    : r.band === 'mid' ? '2년 뒤 다시 기준선 위로 올라설 수도, 머물 수도 있는 갈림길이에요. 지금 챙기는 지원과 일이 방향을 바꿀 수 있어요.'
    : '다시 기준선 위로 올라설 신호가 많은 편이에요. 지금의 어려움이 잠깐일 가능성이 있어요. 그래도 받을 수 있는 지원은 챙겨 두세요.');
  const ms = margins(P), below = ms.filter(x => x.d < 0).length, flow = P.income_2y > 0 ? P.income_now / P.income_2y - 1 : null;
  const sum = el('div', 'sum'); sum.appendChild(el('p', 'head', head)); const ul = el('ul');
  const li = (k, t) => { const l = el('li'); l.appendChild(el('b', '', k + ' ')); l.appendChild(document.createTextNode(t)); ul.appendChild(l); };
  if (ms[0]) li('얼마나 모자라나:', `한 달 ${won(ms[0].d)}, 1년이면 약 ${won(ms[0].d * 12)}이에요.`);
  if (ms.length > 1) li('얼마나 이어졌나:', `최근 3년 중 ${below}번(${ms.filter(x => x.d < 0).map(x => x.t).join('·')}) 기준선 아래였어요.`);
  if (flow !== null) li('소득 흐름:', `2년 전 월 ${fmt(P.income_2y)}만원 → 지금 월 ${fmt(P.income_now)}만원(${flow >= 0 ? '+' : ''}${Math.round(flow * 100)}%).`);
  li('그래서:', "아래 '다음 걸음'에 지금 바로 확인할 지원을 골라 두었어요.");
  sum.appendChild(ul); box.appendChild(sum);
  if (reasons.length) {
    box.appendChild(el('p', '', '이렇게 본 이유 3가지')).style.cssText = 'margin:18px 0 0;font-weight:700;font-size:14px';
    box.appendChild(el('p', 'rhelp', "'머물게 하는 부분'은 기준선 아래에 더 오래 머무는 쪽으로, '올라서게 돕는 부분'은 다시 올라서는 쪽으로 작용했어요. 영향이 큰 것부터 보여 드려요."));
    const list = el('div', 'rlist'); const mx = Math.max(...reasons.map(x => Math.abs(x.effect || 0)), 1e-9);
    reasons.forEach(x => {
      const upx = (x.effect || 0) >= 0, k = Math.abs(x.effect || 0) / mx, c = el('div', 'rs'), t = el('div', 'rs-top');
      t.appendChild(el('span', 'chip2 ' + (upx ? 'up' : 'dn'), upx ? '머물게 하는 부분' : '올라서게 돕는 부분'));
      t.appendChild(el('b', '', flabel(x))); t.appendChild(el('span', 'str', '영향 ' + (k >= .66 ? '큼' : k >= .33 ? '중간' : '작음')));
      c.appendChild(t); const rt = reasonText(x.feature, P, upx); if (rt) c.appendChild(el('p', '', rt)); list.appendChild(c);
    });
    box.appendChild(list);
  }
  if (!r.abstain && typeof r.top_pct === 'number') {
    const more = el('details', 'more'); more.appendChild(el('summary', '', '이 풀이, 믿어도 될까요? (근거 자세히 보기)'));
    const bb = binOf(TESTB.bins, r.top_pct), on = Math.round(bb[2]);
    const s1 = el('div', 'mlsec'); s1.style.borderTop = '0'; s1.appendChild(el('h4', '', '비슷한 신호가 나온 분들은 실제로 어땠을까'));
    s1.appendChild(el('p', '', `이번 풀이와 비슷한 신호가 나온 분 100명 중 ${per100(bb[2])}이 2년 안에 다시 기준선 위로 올라섰어요. 기준선 아래였던 50~69세 전체로는 100명 중 약 ${Math.round(TESTB.up)}명이에요.`));
    const d = el('div', 'dots'); d.setAttribute('role', 'img'); d.setAttribute('aria-label', `100명 중 ${per100(bb[2])} 다시 올라섬, 전체 ${Math.round(TESTB.up)}명`);
    for (let i = 0; i < 100; i++) { const c = el('i'); if (i < on) c.className = 'on up'; if (i === Math.round(TESTB.up) - 1) c.classList.add('avg'); d.appendChild(c); }
    s1.appendChild(d);
    const lg = el('div', 'legend'); lg.innerHTML = '<span><b style="background:var(--ok)"></b>2년 안에 다시 올라선 분</span><span><b style="outline:1.5px solid var(--text2)"></b>전체 평균</span>'; s1.appendChild(lg);
    s1.appendChild(el('p', 'why', `한국복지패널에서 학습에 쓰지 않은 연도에 기준선 아래였던 50~69세 ${TESTB.n.toLocaleString('ko-KR')}명으로 확인한 결과예요. 지금 소득 하나만 볼 때보다 네 기둥을 다 볼 때 누가 다시 올라설지 더 잘 맞혔어요.`));
    s1.appendChild(el('p', 'defn', '생활 기준선: 우리나라 가구 소득을 한 줄로 놓았을 때 한가운데 값의 절반(OECD 기준)을 가구원 수에 맞춘 금액이에요.'));
    more.appendChild(s1); box.appendChild(more);
  }
  if (r.abstain) box.appendChild(el('p', 'mlnote', '판단 보류: 신호가 양쪽으로 섞여 확신이 낮을 때는 결론 대신 이유만 보여 드려요.'));
  box.appendChild(el('p', 'mlnote', '이유는 모델이 이 답에서 풀이를 움직인 크기예요. 원인이라는 뜻은 아니고, 예측일 뿐 미래를 보장하지 않아요.'));
  if (lastP) renderGuide(lastP, r);
}
const LVL = p =>''')
rep(".dots i.on{background:var(--blood2);box-shadow:0 0 6px rgba(212,166,55,.55)}",
    ".dots i.on{background:var(--blood2);box-shadow:0 0 6px rgba(212,166,55,.55)}\n.dots i.on.up{background:var(--ok);box-shadow:0 0 6px rgba(95,158,128,.5)}")
open(out, 'w', encoding='utf-8').write(s); print('ok')
