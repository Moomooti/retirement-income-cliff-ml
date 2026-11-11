// 모델별 상세 설계도 – 검정을 통과한 models_spec.json만 읽어서 그린다 (이름·숫자를 여기서 쓰지 않음)
const { chromium } = require('playwright');
const fs = require('fs');
const SPEC = JSON.parse(fs.readFileSync(process.argv[2] || '/home/claude/work/design_check/models_spec.json', 'utf8'));
const OUT = (process.argv[3] || __dirname + '/models') + '/'; fs.mkdirSync(OUT, { recursive: true });

const C = { data: '#f7c98b', prep: '#f3dc8a', split: '#d9c7f0', model: '#f4b3c2', base: '#e4e4e4', eval: '#a9dedd', serve: '#e6c56a', off: '#f1f1f1' };
const R = 34;
const ICON = {
  db: '<ellipse cx="0" cy="-9" rx="12" ry="5"/><path d="M-12 -9v16c0 3 5 5 12 5s12-2 12-5v-16"/><path d="M-12 -1c0 3 5 5 12 5s12-2 12-5"/>',
  merge: '<path d="M-13 -9h9l8 9h9M-13 9h9l8-9"/><path d="M9 -4l4 4-4 4"/>',
  filter: '<path d="M-13 -11h26l-10 12v10l-6 3v-13z"/>',
  clip: '<path d="M-13 -9h26M-13 9h26"/><path d="M-8 -9v18M8 -9v18" stroke-dasharray="3 3"/>',
  scale: '<path d="M0 -13v26M-12 13h24M-13 -6h26"/><path d="M-13 -6l-4 9h8zM13 -6l-4 9h8z"/>',
  cut: '<circle cx="-7" cy="8" r="4"/><circle cx="7" cy="8" r="4"/><path d="M-4 5l13-18M4 5l-13-18"/>',
  table: '<rect x="-13" y="-11" width="26" height="22" rx="2"/><path d="M-13 -4h26M-13 3h26M-4 -11v22"/>',
  lock: '<rect x="-11" y="-3" width="22" height="15" rx="2"/><path d="M-7 -3v-5a7 7 0 0 1 14 0v5"/>',
  ruler: '<rect x="-14" y="-6" width="28" height="12" rx="2"/><path d="M-8 -6v5M-2 -6v7M4 -6v5M10 -6v7"/>',
  grid: '<rect x="-12" y="-12" width="10" height="10"/><rect x="2" y="-12" width="10" height="10"/><rect x="-12" y="2" width="10" height="10"/><rect x="2" y="2" width="10" height="10"/>',
  tree: '<circle cx="0" cy="-10" r="4"/><circle cx="-10" cy="9" r="4"/><circle cx="10" cy="9" r="4"/><path d="M0 -6v6M-10 5v-5h20v5"/>',
  line: '<path d="M-13 12h26M-13 12v-25"/><path d="M-10 8c6 0 6-14 20-16"/>',
  mix: '<path d="M-13 -8h8l10 16h8M-13 8h8l10-16h8"/>',
  bars: '<path d="M-12 -9h22M-12 0h15M-12 9h8" stroke-width="4"/>',
  q: '<path d="M-5 -6a6 6 0 1 1 7 6c-2 1-2 2-2 5"/><circle cx="0" cy="11" r="1.5"/>',
  flask: '<path d="M-5 -13h10M-3 -13v9l-9 15h24l-9-15v-9"/>',
  check: '<path d="M-12 1l8 8 16-17"/>',
  phone: '<rect x="-9" y="-14" width="18" height="28" rx="3"/><path d="M-3 10h6"/>',
  plug: '<path d="M-6 -14v8M6 -14v8M-10 -6h20v6a10 10 0 0 1-20 0zM0 10v6"/>',
  web: '<rect x="-14" y="-11" width="28" height="22" rx="2"/><path d="M-14 -4h28"/><circle cx="-10" cy="-7.5" r="1"/>',
  curve: '<path d="M-13 12h26M-13 12v-25"/><path d="M-10 9c4-12 10-16 21-17"/><circle cx="-10" cy="9" r="1.5"/><circle cx="11" cy="-8" r="1.5"/>',
  dice: '<rect x="-12" y="-12" width="24" height="24" rx="4"/><circle cx="-5" cy="-5" r="2"/><circle cx="5" cy="5" r="2"/><circle cx="5" cy="-5" r="2"/><circle cx="-5" cy="5" r="2"/>',
  swap: '<path d="M-12 -5h22l-5-5M12 5h-22l5 5"/>',
  tag: '<path d="M-12 -12h11l13 13-11 11-13-13z"/><circle cx="-6" cy="-6" r="2"/>',
  door: '<rect x="-10" y="-13" width="20" height="26" rx="2"/><circle cx="5" cy="1" r="1.6"/>',
  save: '<rect x="-12" y="-12" width="24" height="24" rx="2"/><path d="M-6 -12v8h12v-8M-7 12v-9h14v9"/>',
};
const f3 = v => Number(v).toFixed(3), pc = v => (v * 100).toFixed(1) + '%', n0 = v => Number(v).toLocaleString('en-US'), sg = v => (v >= 0 ? '+' : '') + f3(v);
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const tw = s => [...String(s)].reduce((w, ch) => w + (/[가-힣ㄱ-ㅎ·×→–−]/.test(ch) ? 13 : 7.4), 0);

function draw(m, N, E, card, extra = '', H = 1060, minW = 0) {
  const W = Math.max(minW, Math.max(...Object.values(N).map(n => n[0])) + 230);
  const edge = ([a, b, lab, t = .5, side]) => {
    const [x1, y1] = N[a], [x2, y2] = N[b]; let P;
    if (Math.abs(x1 - x2) < 5) { const s = y2 > y1 ? 1 : -1; const off = 18 + 17 * (N[a][5] || []).length;
      P = [[x1, y1 + s * (R + (s > 0 ? off + 10 : 4))], [x1, y1 + s * (R + off + 30)], [x2, y2 - s * (R + 24)], [x2, y2 - s * (R + 4)]]; }
    else { const sx = x1 + R + 6, ex = x2 - R - 6, dx = Math.max(40, (ex - sx) * .5); P = [[sx, y1], [sx + dx, y1], [ex - dx, y2], [ex, y2]]; }
    const d = `M${P[0][0]} ${P[0][1]} C ${P[1][0]} ${P[1][1]}, ${P[2][0]} ${P[2][1]}, ${P[3][0]} ${P[3][1]}`;
    const bz = k => (1 - t) ** 3 * P[0][k] + 3 * (1 - t) ** 2 * t * P[1][k] + 3 * (1 - t) * t ** 2 * P[2][k] + t ** 3 * P[3][k];
    const w = tw(lab) + 18;
    return { line: `<path d="${d}" class="e"/><circle cx="${P[3][0]}" cy="${P[3][1]}" r="3.5" class="dot"/>`,
      tag: lab ? `<g transform="translate(${bz(0)},${bz(1)})"><rect x="${-w / 2}" y="-11" width="${w}" height="22" rx="11" class="tg"/><text y="4.5" class="el">${esc(lab)}</text></g>` : '' };
  };
  const node = ([x, y, t, ic, name, sub = []]) => `<g transform="translate(${x},${y})">
    <path d="M ${R * .55} ${-R * 1.12} A ${R * 1.25} ${R * 1.25} 0 0 1 ${R * .55} ${R * 1.12}" class="arc"/>
    <circle r="${R}" fill="${C[t]}" class="n${t === 'off' ? ' off' : ''}"/><g class="ic" transform="scale(1.05)">${ICON[ic]}</g>
    <text y="${R + 21}" class="nm">${esc(name)}</text>${sub.map((s, i) => `<text y="${R + 39 + i * 17}" class="sb">${esc(s)}</text>`).join('')}</g>`;
  // 입력 카드
  let cy = 112, cardSvg = '';
  const CW = 560;
  cardSvg += `<text x="44" y="${cy}" class="ch">${esc(card.title)}</text>`; cy += 12;
  if (card.sub) { cardSvg += `<text x="44" y="${cy + 14}" class="cs">${esc(card.sub)}</text>`; cy += 22; }
  for (const [gname, rows, kind] of card.groups) {
    cy += 22; cardSvg += `<rect x="40" y="${cy - 15}" width="${CW}" height="22" rx="4" fill="${kind === 'extra' ? '#fbefd9' : kind === 'flag' ? '#eee8f7' : '#eef6f6'}"/><text x="50" y="${cy}" class="cg">${esc(gname)} · ${rows.length}개</text>`;
    for (const r of rows) {
      cy += 18; cardSvg += `<text x="56" y="${cy}" class="cv">${esc(r[0])}</text><text x="250" y="${cy}" class="cl">${esc(r[1])}</text>` +
        (r[2] !== undefined ? `<text x="${40 + CW - 8}" y="${cy}" class="cf${r[2] < 50 ? ' low' : ''}">${r[2]}%</text>` : '');
    }
    cy += 4;
  }
  if (card.foot) for (const ln of card.foot) { cy += 20; cardSvg += `<text x="44" y="${cy}" class="cs">${esc(ln)}</text>`; }
  H = Math.max(H, cy + 70);
  cardSvg = `<rect x="24" y="80" width="${CW + 32}" height="${cy - 50}" rx="10" class="card"/>` + cardSvg;
  const es = E.map(edge);
  const head = `<text x="24" y="44" class="tt">${esc(m.titleLine)}</text><text x="24" y="68" class="ts">${esc(m.subLine)}</text>`;
  const legend = [['data', '데이터'], ['prep', '정리'], ['split', '분할'], ['base', '기준선'], ['model', '모델·설명'], ['eval', '평가'], ['serve', '서비스']]
    .map(([k, t], i) => `<g transform="translate(${W - 1180 + i * 165},${H - 26})"><circle r="9" fill="${C[k]}" stroke="#8a8a8a" stroke-width="1"/><text x="16" y="5" class="lg">${t}</text></g>`).join('');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="Noto Sans CJK KR, sans-serif">
<style>
 .e{fill:none;stroke:#9aa3ad;stroke-width:2.2} .dot{fill:#9aa3ad}
 .el{font-size:13px;fill:#2f3439;text-anchor:middle;font-weight:600} .tg{fill:#fff;stroke:#b9c0c8;stroke-width:1.2}
 .n{stroke:#fff;stroke-width:3} .n.off{stroke:#c9c9c9;stroke-dasharray:4 4} .arc{fill:none;stroke:#c3c3c3;stroke-width:2;stroke-dasharray:4 5}
 .ic{fill:none;stroke:#3a3a3a;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
 .nm{font-size:16px;font-weight:700;fill:#262626;text-anchor:middle} .sb{font-size:12.5px;fill:#5f5f5f;text-anchor:middle}
 .lg{font-size:13px;fill:#3a3a3a} .tt{font-size:24px;font-weight:800;fill:#262626} .ts{font-size:14px;fill:#6b6b6b}
 .card{fill:#fcfbf8;stroke:#e2dccd;stroke-width:1.2} .ch{font-size:17px;font-weight:800;fill:#262626} .cs{font-size:12.5px;fill:#6b6b6b}
 .cg{font-size:13px;font-weight:700;fill:#3a3a3a} .cv{font-size:12px;fill:#2f3439;font-family:'DejaVu Sans Mono',monospace} .cl{font-size:12.5px;fill:#4a4a4a}
 .cf{font-size:12px;fill:#8a8a8a;text-anchor:end} .cf.low{fill:#b0602a;font-weight:700}
 .mt{font-size:13px;fill:#2f3439;text-anchor:middle} .mh{font-size:12.5px;font-weight:700;fill:#3a3a3a;text-anchor:middle} .note{font-size:13px;fill:#6b6b6b}
</style>
<rect width="${W}" height="${H}" fill="#fff"/>${head}${cardSvg}
${es.map(e => e.line).join('')}${Object.values(N).map(node).join('')}${es.map(e => e.tag).join('')}${extra}${legend}</svg>`;
  return { svg, W, H };
}

const X0 = 720, CS = 300, col = i => X0 + i * CS;
const out = [];
for (const m of SPEC.models) {
  let N, E, card, extra = '', H = 1060;
  if (m.kind === 'task') {
    H = 1180;
    m.titleLine = `${m.title} 모델`; m.subLine = `역할: ${m.role} · 정답: ${m.target} · 시험 AUC ${f3(m.auc.fin)}`;
    card = { title: `입력 ${m.n_feat}개 = 공통 17 + 이 패널 추가 ${m.n_extra}`, sub: '오른쪽 % = 학습셋에서 값이 채워진 비율 (비어 있으면 LightGBM은 그대로, 로지스틱은 중앙값+결측 표시)',
      groups: [...m.groups_common.map(([g, r]) => ['공통 · ' + g, r, 'common']), ...m.groups_extra.map(([g, r]) => ['추가 · ' + g, r, 'extra'])] };
    const sh = m.shap, cf = m.conf;
    N = {
      train: [col(0), 330, 'split', 'table', '학습셋', [`${n0(m.n_tr)}행 · ${m.tr_years}`]],
      test: [col(0), 880, 'split', 'lock', '시험셋 (봉인)', [`${n0(m.n_te)}행 · ${m.te_years}`, `실제 하락 ${pc(m.pos_te)}`]],
      sel: [col(1), 330, 'prep', 'filter', '열 고르기', [`공통 17 + 추가 ${m.n_extra} = ${m.n_feat}열`, '20% 미만 채워진 x_ 열 제외', '원금액 → 소득 배수 · 로그']],
      win: [col(2), 330, 'prep', 'clip', '극단값 자르기', ['학습셋 0.5~99.5% 분위', '시험셋에도 같은 경계', '범주 · 값 3종 이하는 제외']],
      inner: [col(3), 330, 'split', 'cut', '내부 분할', [`내부 학습 ${m.it_years} · ${n0(m.n_it)}행`, `내부 검증 ${m.iv_years} · ${n0(m.n_iv)}행`]],
      grid: [col(4), 130, 'model', 'grid', '격자 탐색 2×2', ['leaves 15/31 × min_child 40/150', '학습률 0.03 · 행·열 0.8 · L2 1', '최대 3000회 · 조기 종료 100']],
      lgb: [col(5), 130, 'model', 'tree', 'LightGBM', [`고름: leaves ${m.lgb.leaves} · min_child ${m.lgb.min_child}`, `반복 ${m.lgb.iters}회 (멈춘 지점 ×1.1)`, '학습셋 전체로 재학습', `시험 AUC ${f3(m.auc.lgb)}`]],
      imp: [col(3), 600, 'prep', 'scale', '결측·표준화', ['숫자: 중앙값 대체 + 결측 표시', '→ 표준화', m.cats.length ? `범주 ${m.cats.length}개: 원-핫(50건 미만 묶음)` : '범주 열 없음']],
      lr: [col(5), 560, 'model', 'line', '로지스틱(L2)', ['C = 1.0 · 학습셋 전체', `시험 AUC ${f3(m.auc.lr)}`]],
      ens: [col(6), 330, 'model', 'mix', '순위 평균 (최종)', ['시험셋 안에서', 'LightGBM 순위 + 로지스틱 순위', `시험 AUC ${f3(m.auc.fin)}`]],
      base: [col(2), 1010, 'base', 'ruler', '기준선 B0 · B1', [`B0 지금 소득만 ${f3(m.auc.b0)}`, `B1 소득·나이·취업 로지스틱 ${f3(m.auc.b1)}`]],
      score: [col(6), 880, 'eval', 'flask', 'Test and Score', [`최종 ${f3(m.auc.fin)} vs 지금 소득 ${f3(m.auc.b0)}`, `차이 ${sg(m.delta)} [${sg(m.lo)}, ${sg(m.hi)}]`, 'DeLong 95% 구간']],
    };
    E = [['train', 'sel', `${m.n_feat}열`], ['sel', 'win', '고른 열'], ['win', 'inner', '자른 값'], ['inner', 'grid', '내부 학습 · 검증'], ['grid', 'lgb', '고른 설정'],
      ['win', 'imp', '학습셋 전체', .5], ['imp', 'lr', '변환된 열'], ['lgb', 'ens', 'LightGBM 점수'], ['lr', 'ens', '로지스틱 점수'],
      ['train', 'base', '지금 소득 · 나이 · 취업', .35], ['base', 'score', '비교 기준', .3], ['test', 'score', '시험 데이터 (같은 경계로 자름)', .3], ['ens', 'score', '최종 점수']];
    if (sh) {
      N.shap = [col(7), 130, 'model', 'bars', '이유 3가지', ['LightGBM 기여 분해(TreeSHAP)', `상위 3개를 바꾸면 무작위 3개의`, `${sh.ratio.toFixed(1)}배만큼 점수가 변함`,
        `위험 상위 20%의 1순위 이유:`, `${sh.top[0][1]} ${Math.round(sh.top[0][2] * 100)}%`]];
      N.conf = [col(4), 700, 'model', 'q', '판단 보류', ['내부 학습 LightGBM 점수로', `내부 검증 ${n0(cf.n_cal)}행에서 경계(α=0.10)`, `포함률 하락 ${pc(cf.cov_pos)} · 비하락 ${pc(cf.cov_neg)}`, `보류 ${pc(cf.abstain)}`]];
      E.push(['lgb', 'shap', '기여 분해'], ['inner', 'conf', '내부 학습 → 검증', .78], ['conf', 'score', '보류 경계', .5]);
    } else {
      N.shap = [col(7), 150, 'off', 'bars', '이유 · 판단 보류', ['이식 과제라 실험하지 않음', '(판정 3 + 필요생활비 + 노동만)']];
    }
  } else if (m.kind === 'pooled') {
    m.titleLine = m.title; m.subLine = `4개 과제 학습셋을 합쳐 하나의 LightGBM으로 학습 · 목적: 데이터가 늘수록 좋아지는지, 외운 게 아닌지 확인 (서비스에는 안 씀)`;
    card = { title: `입력 23개 = 공통 17 + 판정 기준 소득 2 + 패널 표시 4`, sub: '패널 표시 = 그 행이 어느 패널인지 0/1 (패널마다 기준선·조사 방식이 달라서)',
      groups: m.inputs.map(([g, r], i) => [g, r, i === 0 ? 'common' : i === 1 ? 'extra' : 'flag']) };
    N = {}; m.parts.forEach(([nm, a, b], i) => { N['p' + i] = [col(0), 140 + i * 165, 'split', 'table', nm + ' 학습셋', [`${n0(a)}행`]]; });
    Object.assign(N, {
      cat: [col(1), 390, 'prep', 'merge', '합치기', [`${n0(m.n_tr)}행`, '공통 17 + 소득 2 + 패널 표시 4']],
      lgb: [col(2), 390, 'model', 'tree', 'LightGBM (고정 설정)', ['격자 탐색 없음', 'leaves 31 · min_child 80', '학습률 0.03 · 행·열 0.8']],
      lc: [col(4), 130, 'eval', 'curve', '학습곡선', [`${n0(m.lc.n0)} → ${n0(m.lc.n1)}행 (600회)`, `시험 AUC ${f3(m.lc.a0)} → ${f3(m.lc.a1)}`, `학습−시험 격차 ${f3(m.lc.g0)} → ${f3(m.lc.g1)}`]],
      st: [col(4), 330, 'eval', 'curve', '반복 곡선 (800회)', [`마지막 학습 AUC ${f3(m.staged.tr)}`, `마지막 시험 AUC ${f3(m.staged.te)}`, `시험 최고 ${f3(m.staged.te_max)} – 무너지지 않음`]],
      perm: [col(4), 530, 'eval', 'dice', '라벨 셔플 (300회 × 5번)', ['정답만 무작위로 섞어 학습', `시험 AUC 평균 ${f3(m.perm)} ≈ 동전`]],
      band: [col(4), 730, 'eval', 'ruler', '소득 구간 안에서', m.bands.map(b => `${b.lo}~${b.hi > 50 ? '' : b.hi}배: 모델 ${f3(b.ml)} vs 소득 ${f3(b.b0)}`)],
      te: [col(1), 880, 'split', 'lock', '시험셋 합', [`${n0(m.n_te)}행 (패널별 최근 2개 연도)`]],
      sc: [col(2), 760, 'eval', 'flask', 'Test and Score', [`전체 ${f3(m.pool_all)} vs 지금 소득 ${f3(m.pool_b0)}`, ...Object.entries(m.pool_auc).map(([k, v]) => `${k} ${f3(v)}`)]],
    });
    E = [...m.parts.map((_, i) => ['p' + i, 'cat', '', .5]), ['cat', 'lgb', '23열'], ['lgb', 'lc', '1~100% 표본'], ['lgb', 'st', '반복마다 기록'], ['lgb', 'perm', '정답 섞기'],
      ['lgb', 'sc', '800회 모델'], ['te', 'sc', '시험 데이터'], ['sc', 'band', '시험 점수를 소득 구간별로']];
    H = 1080;
  } else if (m.kind === 'transfer') {
    m.titleLine = m.title; m.subLine = '한 패널에서 배운 규칙이 다른 조사에서도 통하는지: 공통 입력만으로 6개 패널끼리 서로 적용 (서비스에는 안 씀)';
    card = { title: '입력 18개 = 공통 17 + 지금 소득', sub: '모든 패널에 같은 이름으로 있는 열만 써야 다른 패널에 그대로 넣을 수 있다',
      groups: m.inputs.map(([g, r], i) => [g, r, i === 0 ? 'common' : 'extra']) };
    N = {
      a: [col(0), 300, 'split', 'table', '패널 A 학습셋', ['6개 패널 각각']],
      lgb: [col(1), 300, 'model', 'tree', 'LightGBM (고정 설정)', ['500회 · leaves 15', 'min_child 80 · 학습률 0.03']],
      b: [col(0), 760, 'split', 'lock', '패널 B 시험셋', ['6개 패널 각각']],
      ap: [col(2), 530, 'eval', 'swap', 'A 모델 → B 시험셋', ['순위 그대로 AUC 계산', '대각선 = 자기 패널']],
      bv: [col(2), 880, 'split', 'cut', '패널 B 내부 검증', ['B 학습셋 마지막 2개 연도']],
      pl: [col(3), 880, 'model', 'scale', 'Platt 재보정', ['로그 오즈 → 로지스틱 1개', '확률 크기만 B에 맞춤']],
      cal: [col(4), 880, 'eval', 'check', '평균 확률 vs 실제', [`보정 전 차이 ${pc(m.cal.raw_gap)}p`, `보정 후 차이 ${pc(m.cal.cal_gap)}p`, '(30개 교차 조합 평균)']],
    };
    E = [['a', 'lgb', '18열'], ['lgb', 'ap', 'A 모델'], ['b', 'ap', '18열'], ['bv', 'pl', 'A 모델 점수'], ['pl', 'cal', '보정식'], ['ap', 'cal', 'B 시험 점수', .6], ['lgb', 'bv', '', .5]];
    // 6×6 표
    const gx = col(3) + 30, gy = 120, cw = 108, chh = 46, mx = m.matrix; m._minW = gx + cw * 7 + 60;
    extra += `<text x="${gx + cw * 3.5}" y="${gy - 14}" class="mh">시험 AUC (행 = 배운 패널 A, 열 = 적용한 패널 B)</text>`;
    m.names.forEach((nm, j) => { extra += `<text x="${gx + cw * (j + 1) + cw / 2}" y="${gy + 30}" class="mh">${esc(nm.replace('패널', ''))}</text>`; });
    m.names.forEach((nm, i) => {
      extra += `<text x="${gx + cw / 2}" y="${gy + chh * (i + 1) + 30}" class="mh">${esc(nm.replace('패널', ''))}</text>`;
      mx[i].forEach((v, j) => { const k = (v - 0.68) / (0.86 - 0.68), col_ = `rgba(64,150,148,${(0.12 + 0.6 * Math.max(0, Math.min(1, k))).toFixed(2)})`;
        extra += `<rect x="${gx + cw * (j + 1) + 2}" y="${gy + chh * (i + 1) + 2}" width="${cw - 4}" height="${chh - 4}" rx="5" fill="${col_}" ${i === j ? 'stroke="#2f3439" stroke-width="2"' : ''}/>` +
          `<text x="${gx + cw * (j + 1) + cw / 2}" y="${gy + chh * (i + 1) + 29}" class="mt">${f3(v)}</text>`; });
    });
    extra += `<text x="${gx}" y="${gy + chh * 7 + 30}" class="note">굵은 테두리 = 자기 패널. 열(B)마다 색이 비슷하면 "어느 패널에서 배워도 B에서 비슷하게 통한다"는 뜻.</text>`;
  } else if (m.kind === 'service' || m.kind === 'b20') {
    const isB = m.kind === 'b20';
    m.titleLine = isB ? m.title : `${m.title}${m.tag === 'S21' ? ' (건강 포함)' : ''}`;
    m.subLine = isB ? `대상: 지금 기준선 아래(0 < r < 1)인 50~69세 · 정답: 2년 뒤에도 기준선 아래에 머묾 · 시험 AUC ${f3(m.auc.fin)}`
                    : `대상: 지금 기준선 위인 50~69세 · 정답: 2년 뒤 반복 하락 · 화면 21문항으로 만들 수 있는 입력만 · 시험 AUC ${f3(m.auc.svc)}`;
    card = { title: `입력 ${isB ? 30 : m.n_feat}개 (화면 문항에서 만듦)`, sub: '네 기둥 묶음 · 금액은 2025년 가격, 소득은 그 해 기준선 대비',
      groups: m.groups.map(([g, r]) => [g, r, g === '선택' ? 'extra' : 'common']),
      foot: isB ? ['S20과 같은 30개 입력 · 같은 학습 함수'] : (m.tag === 'S20' ? [`재현: 재정패널 같은 방식(${m.nastab.n_feat}개 입력) AUC ${f3(m.nastab.auc)} vs 지금 소득 ${f3(m.nastab.b0)}`] : ['S20 + 건강 1문항(선택)']) };
    const yT = 260, yS = 910;
    const tg = m.tag || 'B20';
    N = {
      tr: [col(0), yT, 'split', 'table', '복지패널 학습셋', [`${n0(m.n_tr)}행`, isB ? '지금 기준선 아래만' : '연구 모델과 같은 행']],
      win: [col(1), yT, 'prep', 'clip', '극단값 자르기', ['학습셋 0.5~99.5% 경계', '→ 경계값을 파일에 저장']],
      grid: [col(2), yT - 130, 'model', 'tree', 'LightGBM', [`격자 2×2 → leaves ${m.lgb.leaves} · min ${m.lgb.min_child}`, `반복 ${m.lgb.iters}회 · 학습셋 전체`, `시험 AUC ${f3(m.auc.lgb)}`]],
      lr: [col(2), yT + 110, 'model', 'line', '로지스틱(L2)', ['중앙값+결측 표시 · 표준화', `시험 AUC ${f3(m.auc.lr)}`]],
      mc: [col(2), yT + 330, 'model', 'q', '보류용 LightGBM', ['내부 학습으로만 학습', '내부 검증에서 경계 q1·q0', 'α = 0.10']],
      ref: [col(3), yT - 10, 'prep', 'ruler', '분위 기준표', [`봉인 시험셋 ${n0(m.n_te)}행 점수 분포`, '1001개 분위 · LightGBM · 로지스틱 · 최종']],
      sc: [col(4), yT - 130, 'eval', 'flask', 'Test and Score', isB ? [`최종 ${f3(m.auc.fin)} vs 지금 소득 ${f3(m.auc.b0)}`, `차이 ${sg(m.delta)} (95% 하한 ${sg(m.lo)})`, `포함률 ${pc(m.conf.cov_pos)} · ${pc(m.conf.cov_neg)} · 보류 ${pc(m.conf.abstain)}`, `시험 ${m.te_years} · 실제 머묾 ${pc(m.stay)}`]
        : [`최종 ${f3(m.auc.svc)} (전체 입력 ${f3(m.auc.full)})`, `지금 소득만 ${f3(m.auc.b0)}`, `포함률 ${pc(m.conf.cov_pos)} · ${pc(m.conf.cov_neg)} · 보류 ${pc(m.conf.abstain)}`]],
      file: [col(3), yT + 330, 'serve', 'save', '모델 파일', [`${tg}_lgb · _lr · _conformal`, `${tg}_meta.json (열·경계·분위)`]],
      q: [col(0), yS, 'serve', 'phone', '화면 21문항', ['소득 3칸 · 일 3칸 · 재산 3칸 …']],
      fx: [col(1), yS, 'prep', 'scale', '변수 만들기', ['월소득×12 → 2023년 가격', '÷ √가구원 ÷ 그 해 기준선 → 로그', '재산 ÷ 연소득 · sign·log']],
      ok: [col(2), yS, 'prep', 'door', '대상 확인', ['50~69세 · 지금 소득 > 0', isB ? 'r < 1 → 이 모델(B20)' : 'r ≥ 1 → S20/S21', isB ? '' : '건강 답 있으면 S21'].filter(Boolean)],
      run: [col(3), yS, 'model', 'mix', '점수 → 분위 위치 평균', ['두 점수를 기준표 위치(0~1)로', '바꿔 평균 = 연구의 순위 평균', '→ 상위 몇 %']],
      band: [col(4), yS - 150, 'serve', 'tag', '등급', ['상위 20% high', '20~40% mid · 나머지 low']],
      ab: [col(4), yS + 20, 'serve', 'q', '판단 보류', ['보류용 점수가 두 경계 안에', '모두 들면 보류']],
      why: [col(4), yS + 190, 'serve', 'bars', '이유 3가지', ['LightGBM 기여 절댓값 상위 3', '올린 쪽 · 내린 쪽 모두']],
      api: [col(5), yS + 20, 'serve', 'plug', 'JSON 결과', [`mode = ${isB ? 'below' : 'above'}`, 'band · top_pct · abstain · reasons']],
    };
    E = [['tr', 'win', `${isB ? 30 : m.n_feat}열`], ['win', 'grid', '내부 분할 · 격자', .35], ['win', 'lr', '학습셋 전체', .6], ['win', 'mc', '내부 학습 · 검증', .62],
      ['grid', 'ref', 'LightGBM 점수'], ['lr', 'ref', '로지스틱 점수'], ['ref', 'sc', '최종 점수'], ['ref', 'file', '모델 · 기준표'], ['mc', 'file', '경계 q1 · q0'],
      ['q', 'fx', '답'], ['fx', 'ok', '변수'], ['ok', 'run', '자른 값'], ['file', 'run', '불러오기'], ['run', 'band', '상위 %'], ['run', 'ab', '보류 점수'], ['run', 'why', '기여 분해'],
      ['band', 'api', ''], ['ab', 'api', ''], ['why', 'api', '']];
    extra += `<text x="${col(0) - 50}" y="${yT - 150}" class="mh" style="text-anchor:start">① 학습 (한 번)</text><text x="${col(0) - 50}" y="${yS - 170}" class="mh" style="text-anchor:start">② 화면에서 한 사람씩</text>` +
      `<line x1="${col(0) - 50}" x2="${col(5) + 160}" y1="${yS - 205}" y2="${yS - 205}" stroke="#e2dccd" stroke-dasharray="6 6"/>`;
    if (isB) {
      const bx = col(5) - 110, by = yT - 150, bw = 200, bh = 26;
      extra += `<text x="${bx}" y="${by}" class="cg">시험셋 구간별 실제 머문 비율</text>`;
      m.bins.forEach((b, i) => { const y = by + 16 + i * (bh + 6);
        extra += `<text x="${bx}" y="${y + 18}" class="cl">상위 ${b.lo}~${Math.round(b.hi)}%</text><rect x="${bx + 92}" y="${y}" width="${bw * b.stay}" height="${bh}" rx="4" fill="#e9a8b6"/><text x="${bx + 98 + bw * b.stay}" y="${y + 18}" class="cl">${pc(b.stay)} (${b.n}명)</text>`; });
      m._minW = bx + 92 + bw + 120;
    }
    H = 1240;
  }
  const { svg, W, H: HH } = draw(m, N, E, card, extra, H, m._minW || 0);
  const fn = `${String(out.length + 1).padStart(2, '0')}_${m.id}`;
  fs.writeFileSync(OUT + fn + '.svg', svg); out.push({ fn, svg, W, H: HH, title: m.titleLine });
}
(async () => {
  const b = await chromium.launch();
  for (const o of out) {
    const pg = await b.newPage({ viewport: { width: Math.ceil(o.W), height: Math.ceil(o.H) }, deviceScaleFactor: 2 });
    await pg.setContent(`<html><body style="margin:0">${o.svg}</body></html>`); await pg.waitForTimeout(150);
    await pg.screenshot({ path: OUT + o.fn + '.png' }); await pg.close();
  }
  await b.close(); fs.writeFileSync(OUT + 'index.json', JSON.stringify(out.map(o => ({ fn: o.fn, title: o.title })), null, 1));
  console.log(`검정 ${SPEC.checks}개 통과 사양으로 설계도 ${out.length}장`);
})();
