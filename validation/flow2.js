// 미리사주 모델 설계도 – Orange 위젯 흐름도 스타일 (원형 노드 + 이름 붙은 곡선 연결)
const { chromium } = require('playwright');
const fs = require('fs');
const OUT = __dirname + '/';

const C = { data: '#f7c98b', prep: '#f3dc8a', split: '#d9c7f0', model: '#f4b3c2', base: '#e4e4e4', eval: '#a9dedd', serve: '#e6c56a' };
// x, y, 종류, 이름(두 줄 가능), 아이콘
const SPEC = JSON.parse(fs.readFileSync(process.argv[2] || '/home/claude/work/design_check/flow_spec.json', 'utf8'));
// 위치만 여기서 정하고, 이름·설명·숫자는 검정을 통과한 사양 파일에서 가져온다
const POS = {
  raw: [90, 330, 'db'], conv: [290, 330, 'merge'], schema: [490, 330, 'table'],
  g3: [700, 200, 'db'], g3b: [700, 470, 'db'], adj: [910, 330, 'scale'], label: [1110, 330, 'tag'], split: [1310, 330, 'cut'],
  train: [1510, 200, 'table'], test: [1510, 540, 'lock'],
  b0: [1720, 410, 'ruler'], cmp: [1720, 200, 'grid'], pool: [1720, 690, 'mix'],
  lgb: [1910, 120, 'tree'], lr: [1910, 280, 'line'], ens: [2100, 200, 'mix'],
  shap: [2290, 110, 'bars'], conf: [2290, 290, 'q'],
  score: [2100, 560, 'flask'], check: [2290, 690, 'check'],
  svc: [2480, 200, 'phone'], api: [2650, 340, 'plug'], web: [2650, 560, 'web'],
};
const N = {};
const SX = x => Math.round(150 + (x - 90) * 1.34), W = 3720, H = 860;
for (const k in POS) { const [t, name, sub] = SPEC.nodes[k]; N[k] = [SX(POS[k][0]), POS[k][1], t, [name, sub], POS[k][2]]; }

// from, to, 선 이름
const E = [
  ['raw', 'conv', '원자료'], ['conv', 'schema', '같은 열 이름 표'],
  ['schema', 'g3', '가처분소득 있음', .3], ['schema', 'g3b', '경상소득만'],
  ['g3', 'adj', '판정용', .65], ['g3b', 'adj', '재현·이식용'],
  ['adj', 'label', '기준선 대비 소득 r'], ['label', 'split', 'X + y'],
  ['split', 'train', '과거 연도'], ['split', 'test', '최근 2개 연도'],
  ['train', 'cmp', '학습 데이터'], ['train', 'b0', '학습 데이터', .62], ['train', 'pool', '4개 패널 합침', .7],
  ['cmp', 'lgb', '상위 모델'], ['cmp', 'lr', '상위 모델'], ['lgb', 'ens', '점수'], ['lr', 'ens', '점수'],
  ['ens', 'shap', '최종 모델'], ['ens', 'conf', '최종 모델'],
  ['test', 'score', '시험 데이터', .35], ['ens', 'score', '최종 모델'], ['b0', 'score', '비교 기준', .45],
  ['score', 'check', '패널별 결과'], ['pool', 'check', '학습곡선·셔플', .3],
  ['ens', 'svc', '복지패널로 재학습'], ['shap', 'svc', '이유 3개'], ['conf', 'svc', '보류 경계'],
  ['svc', 'api', '모델 파일', .6], ['api', 'web', '결과(JSON)', .45],
];
const R = 34;
const ICON = {
  db: '<ellipse cx="0" cy="-9" rx="12" ry="5"/><path d="M-12 -9v16c0 3 5 5 12 5s12-2 12-5v-16"/><path d="M-12 -1c0 3 5 5 12 5s12-2 12-5"/>',
  merge: '<path d="M-13 -9h9l8 9h9M-13 9h9l8-9"/><path d="M9 -4l4 4-4 4"/>',
  scale: '<path d="M0 -13v26M-12 13h24M-13 -6h26"/><path d="M-13 -6l-4 9h8zM13 -6l-4 9h8z"/>',
  tag: '<path d="M-12 -12h11l13 13-11 11-13-13z"/><circle cx="-6" cy="-6" r="2"/>',
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
};
function edge([a, b, lab, t = .5]) {
  const [x1, y1] = N[a], [x2, y2] = N[b];
  const sx = x1 + R + 6, ex = x2 - R - 6, dx = Math.max(40, (ex - sx) * .5);
  let P;
  if (Math.abs(x1 - x2) < 5) P = [[x1, y1 + R + 46], [x1, y1 + R + 60], [x2, y2 - R - 20], [x2, y2 - R - 4]];   // 세로로 곧장 내려가는 선
  else P = [[sx, y1], [sx + dx, y1], [ex - dx, y2], [ex, y2]];
  const d = `M${P[0][0]} ${P[0][1]} C ${P[1][0]} ${P[1][1]}, ${P[2][0]} ${P[2][1]}, ${P[3][0]} ${P[3][1]}`;
  const bz = k => (1 - t) ** 3 * P[0][k] + 3 * (1 - t) ** 2 * t * P[1][k] + 3 * (1 - t) * t ** 2 * P[2][k] + t ** 3 * P[3][k];
  const mx = bz(0), my = bz(1);
  const tw = [...lab].reduce((w, ch) => w + (/[가-힣]/.test(ch) ? 14.5 : 8.2), 0) + 16;
  return { line: `<path d="${d}" class="e"/><circle cx="${P[3][0]}" cy="${P[3][1]}" r="3.5" class="dot"/>`,
           tag: `<g transform="translate(${mx},${my})"><rect x="${-tw / 2}" y="-12" width="${tw}" height="24" rx="12" class="tg"/><text y="5" class="el">${lab}</text></g>` };
}
function node(k) {
  const [x, y, t, [name, sub], ic] = N[k];
  return `<g transform="translate(${x},${y})">
    <path d="M ${R * .55} ${-R * 1.12} A ${R * 1.25} ${R * 1.25} 0 0 1 ${R * .55} ${R * 1.12}" class="arc"/>
    <circle r="${R}" fill="${C[t]}" class="n"/>
    <g class="ic" transform="scale(1.05)">${ICON[ic]}</g>
    <text y="${R + 20}" class="nm">${name}</text>
    <text y="${R + 37}" class="sb">${sub}</text></g>`;
}
const legend = [['data', '데이터·판정 패널'], ['prep', '정리·정답'], ['split', '분할'], ['base', '기준선·재현 패널'], ['model', '모델·설명'], ['eval', '평가'], ['serve', '서비스']]
  .map(([k, t], i) => `<g transform="translate(${150 + i * 230},820)"><circle r="10" fill="${C[k]}" stroke="#8a8a8a" stroke-width="1"/><text x="18" y="5" class="lg">${t}</text></g>`).join('');
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" font-family="Noto Sans CJK KR, sans-serif">
<style>
 .e{fill:none;stroke:#9aa3ad;stroke-width:2.2}
 .dot{fill:#9aa3ad}
 .el{font-size:14px;fill:#2f3439;text-anchor:middle;font-weight:600}
 .tg{fill:#fff;stroke:#b9c0c8;stroke-width:1.2}
 .n{stroke:#fff;stroke-width:3}
 .arc{fill:none;stroke:#c3c3c3;stroke-width:2;stroke-dasharray:4 5}
 .ic{fill:none;stroke:#3a3a3a;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
 .nm{font-size:16px;font-weight:700;fill:#262626;text-anchor:middle}
 .sb{font-size:12.5px;fill:#6b6b6b;text-anchor:middle}
 .lg{font-size:14px;fill:#3a3a3a}
</style>
<rect width="${W}" height="${H}" fill="#fff"/>
${E.map(edge).map(e => e.line).join('')}
${Object.keys(N).map(node).join('')}
${E.map(edge).map(e => e.tag).join('')}
${legend}
</svg>`;
fs.writeFileSync(OUT + 'flow.svg', svg);
console.log('검정 통과 항목', SPEC.checks, '개로 만든 사양 사용');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 2 });
  await pg.setContent(`<html><body style="margin:0">${svg}</body></html>`); await pg.waitForTimeout(300);
  await pg.screenshot({ path: OUT + 'flow.png' }); await b.close(); console.log('ok');
})();
